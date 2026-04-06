# Assessment Data Flow

**Date:** 2026-04-06
**Status:** Final Design
**Version:** 2

---

## Data Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    MASTER DATA                          │
│                                                         │
│  itx.info.vehicle.template.bom (body_type level)        │
│  → ~54 parts per body_type                              │
│  → มีอยู่แล้ว ไม่ต้องสร้างใหม่                           │
│                                                         │
│             ↓ generate ครั้งแรกของ spec                   │
│                                                         │
│  product.template (lookup or create per part)            │
│  → key: spec + part_name + origin + condition            │
│  → ได้ standard_price (avg inventory cost) ถ้ามี         │
│                                                         │
│  mrp.bom (spec level, 1 spec = 1 BOM)                   │
│  → parent product = "ซากรถ Civic FD 1.8S (Salvage)"     │
│  → bom_line = products ที่ lookup/create ข้างบน          │
│  → editable: user add/remove parts ได้                  │
│  → ใช้ซ้ำได้เมื่อซื้อรถ spec เดียวกันอีกคัน               │
│                                                         │
├─────────────────────────────────────────────────────────┤
│                  TRANSACTION DATA                       │
│                                                         │
│  itx.revival.assessment                                 │
│  → 1 assessment = 1 ซากรถที่ไปดู                        │
│                                                         │
│  itx.revival.assessment.line                             │
│  → copy จาก mrp.bom lines                               │
│  → product_id → ดึง avg price จาก inventory ได้          │
│  → สายสืบกรอก: is_found, qty_found, actual_condition    │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## States

```
draft → preparing → complete → cancelled (not_buy)
                             → acquired  (sell_whole / dismantle → DOC 2)
```

| State | ความหมาย | ปุ่มที่ใช้ได้ |
|---|---|---|
| draft | กรอกข้อมูลเบื้องต้น | Start Preparing, Cancel |
| preparing | เตรียมข้อมูล + field survey | Generate Lines, Print Checklist, Complete |
| complete | พร้อม make decision | Cancel (not_buy), Create Acquired |
| cancelled | ไม่ซื้อ | Reset to Draft |
| acquired | สร้าง DOC 2 แล้ว | View Acquired |

---

## STATE: draft

ผู้ทำ: Assessor

กรอก:
- spec_id (required) → body_type_id (auto)
- location, vehicle_year, vehicle_color, vehicle_mileage, vehicle_vin
- asking_price
- assessor_id, assessment_date

Validation ก่อน Start Preparing:
- spec_id ต้องมี
- body_type_id ต้องมี (auto จาก spec)

ปุ่ม: **[Start Preparing]** → state = preparing

---

## STATE: preparing

### Step 1 — Generate Lines

ผู้ทำ: H/O
ปุ่ม: **[Generate Lines]**

NOT NULL ก่อนกด:
- spec_id (มีตั้งแต่ draft)
- body_type_id (auto)
- ราคา: ไม่ต้อง (กรอกทีหลัง Step 2)

```
Logic:

1. มี mrp.bom ของ spec นี้แล้วหรือยัง?
   → search mrp.bom WHERE itx_spec_id = assessment.spec_id

2a. ยังไม่มี → สร้างใหม่จาก template:
    ├── อ่าน template.bom WHERE body_type_id = ?
    ├── For each template line:
    │     origin    = bom.default_part_origin_id OR fallback OEM
    │     condition = bom.default_part_condition_id OR fallback FAIR
    │     → lookup/create product.template
    │       key: spec + part_name + origin + condition
    ├── สร้าง salvage vehicle product (parent)
    │     name: "{spec.full_name} (Salvage)"
    │     type: product
    │     itx_is_vehicle_part: False (ตัวรถ ไม่ใช่ part)
    └── สร้าง mrp.bom
          product_tmpl_id = salvage vehicle product
          itx_spec_id = spec_id
          type = 'normal'
          bom_line_ids = products ที่ lookup/create ข้างบน

2b. มีแล้ว → ใช้ BOM เดิม (master ที่อาจ edit แล้ว)

3. Copy mrp.bom.bom_line_ids → assessment.line:
   ┌────────────────────────┬──────────────────────────────┐
   │ mrp.bom.line (source)  │ assessment.line (target)     │
   ├────────────────────────┼──────────────────────────────┤
   │ product_id             │ product_id                   │
   │ product_qty            │ qty_expected                 │
   │ —                      │ qty_found = qty_expected     │
   │ itx_cost_weight        │ cost_weight                  │
   │ itx_expected_price     │ expected_price               │
   │ —                      │ is_found = True              │
   │ —                      │ actual_condition_id = empty  │
   │ —                      │ field_note = empty           │
   └────────────────────────┴──────────────────────────────┘

   part_name_id, part_origin_id, part_condition_id
   → ดึงจาก product_id.itx_part_name_id, .itx_part_origin_id, .itx_condition_id
```

### ครั้งที่ 2+ ของ spec เดียวกัน

```
ซื้อ Civic FD 1.8S อีกคัน → สร้าง Assessment ใหม่
→ Generate Lines → เจอ mrp.bom เดิม (master)
→ copy lines มาเลย ไม่ generate จาก template ใหม่
→ BOM อาจถูก edit แล้ว (เพิ่ม/ลบ parts) → ได้ข้อมูล up-to-date
→ ราคา standard_price ใน product อาจ update จากการขายจริงรอบก่อน
```

### Step 2 — ตั้งราคา

ผู้ทำ: H/O

Header:
- target_price ← กรอก (ราคาที่จะเสนอซื้อ)

Lines:
- expected_price ← กรอกต่อชิ้น (อาจมีค่ามาแล้วจาก BOM master)
- cost_weight ← ปรับถ้าต้องการ

Auto-compute:
- expected_revenue = Σ (line.expected_price × line.qty_expected)
- expected_profit = expected_revenue - target_price
- expected_roi = expected_profit / target_price × 100
- allocated_cost = target_price × weight / Σweight

### Step 3 — Field Survey

ผู้ทำ: สายสืบ (ผ่าน Odoo UI)

Optional: **[Print Checklist]** → PDF ให้สายสืบ

ระดับ Header (สายสืบกรอก):
- vehicle_vin ← เลขตัวถังจริง (ถ้ายังไม่มี)
- overall_condition ← สภาพโดยรวม (flood/accident/normal_wear/fire/other)
- overall_condition_note ← อธิบายเพิ่ม

ระดับ Line (สายสืบกรอกต่อชิ้น):
- is_found ← untick ถ้าไม่เจอ
- qty_found ← จำนวนที่เจอใช้ได้จริง (default = qty_expected)
- actual_condition_id ← สภาพจริง
- field_note ← หมายเหตุ (เช่น "ยาง Bridgestone ปี 2025 ดอก 90%")

onchange is_found=False:
- actual_condition_id = False
- qty_found = 0
- expected_price = 0

### Step 4 — Review & Complete

ผู้ทำ: H/O

- ดูผล survey → ปรับ expected_price / qty ถ้าจำเป็น
- ROI update อัตโนมัติ

ปุ่ม: **[Complete]** → state = complete

Validation:
- ต้องมี lines (line_count > 0)
- ต้องมี target_price > 0

---

## STATE: complete

ผู้ทำ: H/O

กรอก:
- decision: not_buy / sell_whole / dismantle
- decision_note

ปุ่ม **[Not Buy (Cancel)]** (decision=not_buy):
- state → cancelled
- auto: decision_date, decision_by

ปุ่ม **[Create Acquired]** (decision=sell_whole/dismantle):
- สร้าง DOC 2 (itx.revival.acquired)
- copy: spec_id, vehicle details, link assessment_id
- สร้าง salvage vehicle product ระดับ VIN (ถ้ายังไม่มี)
  → ใช้กับ stock in/out จริง
- state → acquired
- auto: decision_date, decision_by

---

## Model Changes Required

### mrp.bom (inherit) — เพิ่ม field
- `itx_spec_id` (Many2one → itx.vehicle.spec) — ระบุ BOM ของ spec ไหน

### assessment.line — เพิ่ม fields
- `qty_expected` (Integer) — จำนวนที่คาดว่ามี (จาก BOM)
- `qty_found` (Integer) — จำนวนที่สายสืบเจอจริง (default = qty_expected)

### assessment (header) — เพิ่ม fields
- `overall_condition` (Selection) — สภาพโดยรวมรถ
- `overall_condition_note` (Text) — อธิบายสภาพเพิ่ม
- `bom_id` (Many2one → mrp.bom) — link ไป spec-level BOM ที่ใช้

### Salvage Vehicle Product
- สร้างอัตโนมัติตอน Generate Lines (spec level)
- name: "{spec.full_name} (Salvage)"
- type: product (storable)
- ยังไม่มี stock จนกว่าจะ purchased (DOC 2)
