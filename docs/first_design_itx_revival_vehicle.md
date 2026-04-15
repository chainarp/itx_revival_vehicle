# itx_revival_vehicle — Odoo Addon Design Document

## Module Info

```
Name:     itx_revival_vehicle
Version:  19.0.1.0.0
Depends:  itx_info_vehicle, mrp, purchase, account, stock
Concept:  วงจรชีวิตซากรถ ตั้งแต่ประเมิน → ซื้อ → แตกชิ้นส่วน → ติดตาม ROI
```

---

## ที่มาและ Business Context

ธุรกิจซื้อซากรถมาแยกชิ้นส่วนขาย มี process ดังนี้

1. สายสืบเจอซากรถ → แจ้ง H/O ว่าเจออะไร ราคาเท่าไหร่
2. H/O สร้างแบบประเมิน → generate list อะไหล่ + ราคาคาดการณ์
3. พิมพ์ checklist ให้สายสืบไปสำรวจหน้างาน
4. H/O ตัดสินใจ: ไม่ซื้อ / ซื้อขายทั้งคัน / ซื้อแตก part
5. ถ้าซื้อ → สร้าง PO → รับเข้าสต็อก → Unbuild → อะไหล่พร้อมขาย

หมายเหตุ: BOM + parts ต้องเตรียมก่อนซื้อรถ (ใช้ตอนประเมินความคุ้มค่า)

---

## Revival Cycle (State Machine)

```
draft → assessed → decided → acquired → dismantling → completed
                      │
                      └── cancelled (ไม่ซื้อ)
```

---

## Relationship กับ itx_info_vehicle

```
itx_info_vehicle provides (infrastructure):
  ✅ itx.vehicle.spec          → ระบุรถ
  ✅ itx.info.vehicle.template.part  → ชื่ออะไหล่มาตรฐาน
  ✅ itx.info.vehicle.template.bom   → body_type → parts mapping
  ✅ product.template (extended)     → อะไหล่แต่ละชิ้น
  ✅ Auto Internal Reference         → รหัสอะไหล่อัตโนมัติ

itx_revival_vehicle uses:
  → spec_id เพื่อรู้รถ
  → template.bom เพื่อ generate assessment lines
  → product.template เพื่อ lookup/create อะไหล่
  → mrp.bom + mrp.unbuild เพื่อแตกชิ้นส่วน
```

---

## Models ทั้งหมด (5 models + 3 inherit)

---

### 1. itx.revival.assessment
แบบประเมินซากรถ — เกิดก่อนซื้อรถ

```
_name: itx.revival.assessment
_description: Vehicle Revival Assessment
_order: name desc
```

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | ASM/2026/0001 |
| spec_id | Many2one itx.vehicle.spec (required) | สเปครถ — KEY #1 |
| body_type_id | Many2one (related spec.generation.body_type, store=True) | ประเภทตัวถัง — KEY #2 |
| brand_id | related store=True | ยี่ห้อ |
| model_id | related store=True | รุ่น |
| generation_id | related store=True | เจน |
| assessor_id | Many2one res.partner | สายสืบ |
| assessment_date | Date | วันที่ประเมิน |
| location | Char | ที่อยู่ซากรถ |
| vehicle_year | Integer | ปีรถ |
| vehicle_color | Char | สีรถ |
| vehicle_mileage | Integer | เลขไมล์ |
| vehicle_vin | Char | เลขตัวถัง (ถ้ารู้ตอนนี้) |
| asking_price | Float | ราคาที่เจ้าของตั้ง |
| target_price | Float | ราคาที่เราจะเสนอซื้อ |
| expected_revenue | Float (computed) | Σ line.expected_price |
| expected_profit | Float (computed) | expected_revenue - target_price |
| expected_roi | Float (computed) | expected_profit / target_price × 100 |
| decision | Selection | not_buy / sell_whole / dismantle |
| decision_note | Text | เหตุผลการตัดสินใจ |
| decision_date | Date | วันที่ตัดสินใจ |
| decision_by | Many2one res.users | ผู้ตัดสินใจ |
| state | Selection | draft / assessed / decided / acquired / cancelled |
| line_ids | One2many itx.revival.assessment.line | รายการอะไหล่ |
| acquired_id | Many2one itx.revival.acquired | ผูกกับการซื้อ (ถ้าตัดสินใจซื้อ) |
| note | Text | หมายเหตุ |
| active | Boolean | default=True |

Buttons / Actions:
- `action_generate_lines` — generate lines จาก template.bom (spec + body_type)
- `action_assessed` — state: draft → assessed
- `action_decide` — state: assessed → decided
- `action_cancel` — state: → cancelled
- `action_create_acquired` — สร้าง acquired_vehicle (state → acquired)
- `action_print_checklist` — พิมพ์ checklist PDF ให้สายสืบ

---

### 2. itx.revival.assessment.line
รายการอะไหล่ในแบบประเมิน

```
_name: itx.revival.assessment.line
_order: sequence, id
```

| Field | Type | คำอธิบาย |
|---|---|---|
| assessment_id | Many2one itx.revival.assessment | หัว |
| sequence | Integer | ลำดับ |
| part_name_id | Many2one itx.info.vehicle.template.part | ชื่ออะไหล่มาตรฐาน |
| part_category_id | Many2one (related part_name.category_id) | หมวดหมู่ |
| product_id | Many2one product.template | product ที่ generate/lookup ได้ |
| expected_price | Float | ราคาที่คาดว่าขายได้ (H/O กรอก) |
| cost_weight | Float | % สัดส่วนต้นทุน (ใช้ตอน Unbuild) |
| is_found | Boolean | สายสืบเจอหรือไม่ |
| actual_condition | Selection | good / fair / poor / missing |
| field_note | Char | หมายเหตุจากหน้างาน |
| allocated_cost | Float (computed) | total_cost × weight / Σweight |

---

### 3. itx.revival.acquired
รถที่ซื้อเข้ามาแล้ว — เกิดหลังจากตัดสินใจซื้อ

```
_name: itx.revival.acquired
_description: Acquired Vehicle
_order: name desc
```

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | ACQ/2026/0001 |
| assessment_id | Many2one itx.revival.assessment | แบบประเมินที่มาจาก |
| spec_id | related assessment.spec_id store=True | สเปครถ |
| body_type_id | related store=True | ประเภทตัวถัง |
| vin | Char (required) | เลขตัวถัง (required ตอนนี้) |
| vehicle_year | Integer | ปีรถ |
| vehicle_color | Char | สีรถ |
| vehicle_mileage | Integer | เลขไมล์ |
| purchase_order_id | Many2one purchase.order | ใบ PO |
| purchase_price | Float | ราคาที่ซื้อจริง |
| purchase_date | Date | วันที่ซื้อ |
| vendor_id | Many2one res.partner | ผู้ขาย (เจ้าของซาก) |
| transport_cost | Float | ค่าขนส่ง |
| dismantling_cost | Float | ค่า outsource รื้อถอน |
| other_cost | Float | ค่าใช้จ่ายอื่น |
| total_cost | Float (computed) | Σ ทุก cost |
| analytic_account_id | Many2one account.analytic.account | 1 คัน = 1 analytic |
| product_id | Many2one product.product | ตัวซากรถเป็น product (ใช้กับ Unbuild) |
| bom_id | Many2one mrp.bom | BOM สำหรับ Unbuild |
| unbuild_ids | One2many mrp.unbuild | Unbuild Orders |
| decision | related assessment.decision store=True | sell_whole / dismantle |
| state | Selection | draft / purchased / stocked / dismantling / completed |
| actual_revenue | Float (computed) | Σ ราคาขายจริงของอะไหล่ที่ขายแล้ว |
| actual_profit | Float (computed) | actual_revenue - total_cost |
| actual_roi | Float (computed) | actual_profit / total_cost × 100 |
| sold_percentage | Float (computed) | จำนวนชิ้นที่ขาย / ทั้งหมด × 100 |
| note | Text | หมายเหตุ |

Buttons / Actions:
- `action_create_po` — สร้าง Purchase Order
- `action_confirm_stock` — ยืนยันรับเข้าสต็อก
- `action_create_bom` — สร้าง mrp.bom จาก assessment lines
- `action_unbuild` — สร้าง mrp.unbuild Order
- `action_complete` — ปิด cycle

---

### 4. itx.revival.acquired.image
รูปถ่ายซากรถ

```
_name: itx.revival.acquired.image
```

| Field | Type | คำอธิบาย |
|---|---|---|
| acquired_id | Many2one itx.revival.acquired | รถที่ถ่าย |
| image | Image | รูปภาพ |
| description | Char | คำอธิบาย เช่น "ห้องเครื่อง", "หน้าซ้าย" |
| sequence | Integer | ลำดับ |

---

### 5. itx.revival.report (Computed / SQL View)
ROI Report ต่อคัน (ตามที่ Proposal DP ระบุ)

```
_name: itx.revival.report
_auto: False (SQL View)
```

| Field | คำอธิบาย |
|---|---|
| acquired_id | รถแต่ละคัน |
| total_cost | ต้นทุนรวม |
| expected_revenue | รายได้คาดการณ์ |
| actual_revenue | รายได้จริง |
| sold_percentage | % ชิ้นส่วนที่ขายแล้ว |
| actual_profit | กำไรจริง |
| actual_margin | % กำไร |
| pricing_efficiency | actual_revenue / expected_revenue × 100 |

---

### Inherit Models

#### mrp.bom (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_acquired_id | Many2one itx.revival.acquired | ผูกกับรถคันไหน |

#### mrp.bom.line (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_cost_weight | Float | % สัดส่วนต้นทุน |
| itx_allocated_cost | Float (computed) | ต้นทุนที่กระจายให้ชิ้นนี้ |
| itx_expected_price | Float | ราคาขายที่คาดการณ์ |

#### mrp.unbuild (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_acquired_id | Many2one itx.revival.acquired | ผูกกับรถคันไหน |

---

## Generate Lines Logic (action_generate_lines)

```
Input:
  spec_id      → รู้ generation → รู้ body_type_id
  body_type_id → KEY สำหรับ lookup

Process:
  1. ดึง template.bom WHERE body_type_id = body_type_id
     → ได้ list of template_part ~54 ชิ้น

  2. For each template_part:
     Lookup product.template WHERE:
       itx_spec_id      = spec_id
       itx_part_name_id = template_part_id
       itx_part_origin  = 'oem'    (default)
       itx_condition    = 'fair'   (default)

     ถ้าพบ  → เอา product.id ไปใส่ line.product_id
     ไม่พบ  → สร้าง product.template ใหม่
               (Auto Internal Reference ทำงานเองจาก itx_info_vehicle)
               → เอา id ใหม่ไปใส่ line.product_id

  3. สร้าง assessment.line ทุกชิ้น
     cost_weight default = 100 / จำนวน parts (เฉลี่ยเท่าๆกัน)

Output:
  assessment.line_ids ครบทุกชิ้น พร้อม product_id
```

---

## Create BOM Logic (action_create_bom)

```
Input:
  acquired_id → assessment → lines (is_found=True เท่านั้น)

Process:
  1. สร้าง mrp.bom
     product_id = acquired.product_id (ตัวซากรถ)
     type       = 'normal'
     itx_acquired_id = acquired_id

  2. For each assessment.line WHERE is_found = True:
     สร้าง mrp.bom.line
       product_id       = line.product_id
       product_qty      = 1
       itx_cost_weight  = line.cost_weight
       itx_expected_price = line.expected_price

  3. ผูก bom_id กลับที่ acquired

Output:
  mrp.bom พร้อม lines เฉพาะชิ้นที่สายสืบเจอจริง
```

---

## Analytic Account Strategy

```
ตอนสร้าง acquired_vehicle:
  → สร้าง analytic.account อัตโนมัติ
  → ชื่อ: "ACQ/2026/0001 - Honda Civic FD 2009"

ทุก transaction ผูก analytic นี้:
  PO (ซื้อรถ)          → debit
  ค่าขนส่ง             → debit
  ค่า outsource รื้อ   → debit
  ขายอะไหล่ชิ้นไหน    → credit

→ ดู P&L ของซากรถแต่ละคันได้ทันที
→ ตรงกับที่ At Thai เสนอใน Proposal DP
```

---

## โครงสร้าง Module

```
itx_revival_vehicle/
├── __manifest__.py
│     name: "ITX Revival Vehicle"
│     version: 19.0.1.0.0
│     depends: ['itx_info_vehicle', 'mrp', 'purchase', 'account', 'stock']
│
├── models/
│   ├── __init__.py
│   ├── itx_revival_assessment.py
│   ├── itx_revival_assessment_line.py
│   ├── itx_revival_acquired.py
│   ├── itx_revival_acquired_image.py
│   ├── itx_revival_report.py        (SQL View)
│   ├── mrp_bom.py                   (inherit)
│   ├── mrp_bom_line.py              (inherit)
│   └── mrp_unbuild.py               (inherit)
│
├── views/
│   ├── itx_revival_assessment_views.xml
│   ├── itx_revival_acquired_views.xml
│   ├── itx_revival_report_views.xml
│   └── menuitems.xml
│
├── wizard/
│   └── itx_revival_generate_lines_wizard.py  (ถ้าทำเป็น wizard)
│
├── report/
│   └── itx_revival_checklist_report.xml      (PDF checklist สายสืบ)
│
├── security/
│   └── ir.model.access.csv
│
└── data/
    └── ir_sequence_data.xml   (ASM/YYYY/NNNN, ACQ/YYYY/NNNN)
```

---

## Menu Structure

```
Revival Vehicle (main menu)
├── Assessments          ← itx.revival.assessment (list/form)
├── Acquired Vehicles    ← itx.revival.acquired (list/form)
├── Reports
│   └── ROI Report       ← itx.revival.report
└── Configuration
    └── (ใช้ของ itx_info_vehicle)
```

---

## หมายเหตุสำหรับ Claude Code

1. ใช้ Odoo 19 Community Edition
2. spec_id.generation_id.body_type_id ต้องมีใน itx_info_vehicle ก่อน
   (ตรวจสอบว่า Generation model มี body_type_id field ไหม)
3. Generate lines: default origin='oem', condition='fair' ตาม UK ของ product.template
4. BOM type ใช้ 'normal' (ใช้กับ mrp.unbuild ได้)
5. Analytic account สร้างอัตโนมัติตอน create acquired (ไม่ให้ user สร้างเอง)
6. cost_weight default = เฉลี่ยเท่ากัน (100/จำนวน parts) แก้ได้ทีหลัง
7. is_found default = True (สายสืบ tick ออกถ้าไม่เจอ ง่ายกว่า)
8. Security: Revival Manager, Revival User
9. PDF Checklist ต้องมี: ชื่ออะไหล่, ราคาคาดการณ์, ช่อง is_found, ช่อง condition, ช่อง note
