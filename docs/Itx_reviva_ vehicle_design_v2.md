# itx_revival_vehicle — Complete Design Document for Claude Code

**Date:** 2026-04-05  
**Version:** 19.0.1.0.0  
**Status:** Ready for Implementation  

---

## 1. Module Overview

```
Name:        itx_revival_vehicle
Description: วงจรชีวิตซากรถ — ประเมิน → ซื้อ → แตกชิ้นส่วน → ขาย
Depends:     itx_info_vehicle, dynamic_approval_workflow,
             mrp, purchase, account, stock
Concept:     "Revival" = ฟื้นคืนชีพซากรถ ปลุกคุณค่าชิ้นส่วนขึ้นมาใหม่
```

---

## 2. Infrastructure ที่ได้จาก itx_info_vehicle (อย่าสร้างซ้ำ)

```
itx.vehicle.spec                      → ระบุรถ (Brand/Model/Generation/Spec)
itx.info.vehicle.mgr.body.type        → ประเภทตัวถัง (Sedan, SUV, Double Cab ฯลฯ)
itx.info.vehicle.template.part        → ชื่ออะไหล่มาตรฐาน ~79 รายการ
itx.info.vehicle.template.bom         → body_type → parts mapping ~378 records
                                         (KEY: body_type_id + part_template_id)
product.template (extended)           → อะไหล่แต่ละชิ้น พร้อม auto internal reference
                                         UK: spec_id + part_name_id + origin + condition
```

### body_type_id อยู่ที่ไหน
ตรวจสอบก่อนว่า `itx.vehicle.generation` มี `body_type_id` field หรือไม่
ถ้าไม่มี ต้องเพิ่มใน itx_info_vehicle ก่อน เพราะ revival ต้องใช้ดึง template.bom

---

## 3. Documents และ Flow ทั้งหมด

```
[DOC 1] Assessment
    └── ประเมินซากรถก่อนซื้อ (สายสืบหาซากเจอ → H/O ประเมิน)

[DOC 2] Acquired Vehicle
    └── รถที่ตัดสินใจซื้อแล้ว (PO + Stock In)

[DOC 3] Dismantling
    └── แตกชิ้นส่วน (Unbuild) → อะไหล่เข้าสต็อก พร้อมขาย
```

### Full Flow

```
สายสืบเจอซาก
      │
      ▼
[DOC 1] Assessment
  state: request → approved → preparing → complete
                                              │
                                         make_decision
                                              │
                              ┌───────────────┼───────────────┐
                              ▼               ▼               ▼
                          not_buy        sell_whole       dismantle
                              │               │               │
                          cancelled          [DOC 2]        [DOC 2]
                                          Acquired        Acquired
                                              │               │
                                         sell process      [DOC 3]
                                                         Dismantling
                                                              │
                                                         stock_out ซากรถ
                                                         stock_in อะไหล่
                                                         → ready to sell
```

---

## 4. Approval Workflow (dynamic_approval_workflow)

### วิธี integrate กับทุก Document

```python
# ทุก model ที่ต้องการ approval ใช้ pattern นี้
class ItxRevivalXxx(models.Model):
    _name = 'itx.revival.xxx'
    _inherit = [
        'approval.mixin',       # จาก dynamic_approval_workflow
        'mail.thread',
        'mail.activity.mixin',
    ]
```

```python
# __manifest__.py
'depends': [
    'itx_info_vehicle',
    'dynamic_approval_workflow',
    'mrp',
    'purchase',
    'account',
    'stock',
]
```

```xml
<!-- ทุก form view เพิ่ม submit button + approval_state badge -->
<button name="action_submit_for_approval"
        type="object"
        string="Submit for Approval"
        class="btn-secondary"
        invisible="state != 'draft' or approval_state not in ('draft', 'returned')"/>
<field name="approval_state" readonly="1" widget="badge"/>
```

### Approval States (จาก module)
```
draft → pending_approval → approved
                        → rejected
                        → returned (แก้แล้วส่งใหม่)
```

### Config จาก UI (DP ทำเองได้)
- กำหนด approver แต่ละ stage ต่อ document
- ใช้ specific user / security group / dynamic field
- DP เปลี่ยน approver เองได้ ไม่ต้องให้ dev แก้ code

---

## 5. DOC 1: itx.revival.assessment

### Purpose
แบบประเมินซากรถ — เกิดก่อนซื้อรถ ใช้ประเมินความคุ้มค่า

### States
```
request → approved → preparing → complete → [make_decision]
                                                    │
                                         cancelled (not_buy)
```

### Fields (Header)

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | ASM/2026/0001 |
| spec_id | Many2one itx.vehicle.spec (required) | สเปครถ — KEY #1 |
| body_type_id | Many2one (related spec.generation.body_type_id, store=True) | ประเภทตัวถัง — KEY #2 |
| brand_id | related store=True | ยี่ห้อ (auto) |
| model_id | related store=True | รุ่น (auto) |
| generation_id | related store=True | เจน (auto) |
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
| state | Selection | request/approved/preparing/complete/cancelled |
| line_ids | One2many itx.revival.assessment.line | รายการอะไหล่ |
| acquired_id | Many2one itx.revival.acquired | ผูกหลังซื้อ |
| note | Text | หมายเหตุ |
| active | Boolean | default=True |

### Buttons / Actions
- `action_generate_lines` — generate lines จาก template.bom (ดู logic ข้อ 8)
- `action_approve` — request → approved
- `action_prepare` — approved → preparing
- `action_complete` — preparing → complete
- `action_cancel` — → cancelled
- `action_make_decision` — บันทึก decision หลัง complete
- `action_create_acquired` — สร้าง DOC 2 (เมื่อ decision = sell_whole/dismantle)
- `action_print_checklist` — พิมพ์ PDF checklist ให้สายสืบ

---

## 6. itx.revival.assessment.line

### Purpose
รายการอะไหล่ในแบบประเมิน — generate จาก template.bom, สายสืบกรอกหน้างาน

| Field | Type | คำอธิบาย |
|---|---|---|
| assessment_id | Many2one itx.revival.assessment | หัวเอกสาร |
| sequence | Integer | ลำดับ |
| part_name_id | Many2one itx.info.vehicle.template.part | ชื่ออะไหล่มาตรฐาน |
| part_category_id | related part_name.category_id | หมวดหมู่ (auto) |
| product_id | Many2one product.template | product (จาก lookup/create) |
| origin | Selection | oem/aftermarket/reconditioned (default: oem) |
| condition | Selection | new/like_new/good/fair (default: fair) |
| expected_price | Float | ราคาที่คาดว่าขายได้ (H/O กรอก) |
| avg_part_cost | Float (computed) | ราคาซื้อรถ × cost_weight / 100 |
| cost_weight | Float | % สัดส่วนต้นทุน (default: เฉลี่ยเท่ากัน) |
| is_found | Boolean | สายสืบเจอหรือไม่ (default: True) |
| actual_condition | Selection | good/fair/poor/missing (สายสืบกรอก) |
| field_note | Char | หมายเหตุจากหน้างาน |

### หมายเหตุ cost_weight
- default = 100 / จำนวน parts (เฉลี่ยเท่ากัน)
- user แก้ cost_weight เองได้
- avg_part_cost = target_price × cost_weight / 100
- ต้องถาม user เพิ่มเติมว่าต้องการ weight จาก market price (product.standard_price) ด้วยหรือไม่

---

## 7. DOC 2: itx.revival.acquired

### Purpose
รถที่ตัดสินใจซื้อแล้ว — มี PO, Stock In, VIN ครบ
เกิดหลัง Assessment complete และ decision = sell_whole หรือ dismantle

### States
```
draft → submitted → approved → purchasing → stocked → completed
              │
           rejected → draft (แก้แล้วส่งใหม่)
```

### Approval
ใช้ `approval.mixin` จาก dynamic_approval_workflow

### Fields (Header)

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | ACQ/2026/0001 |
| assessment_id | Many2one itx.revival.assessment (required) | แบบประเมินที่มาจาก |
| spec_id | related assessment.spec_id store=True | สเปครถ |
| body_type_id | related store=True | ประเภทตัวถัง |
| decision | related assessment.decision store=True | sell_whole / dismantle |
| vin | Char (required) | เลขตัวถัง (required ณ จุดนี้) |
| vehicle_year | Integer | ปีรถ |
| vehicle_color | Char | สีรถ |
| vehicle_mileage | Integer | เลขไมล์ |
| vendor_id | Many2one res.partner | ผู้ขาย (เจ้าของซาก) |
| purchase_order_id | Many2one purchase.order | ใบ PO |
| purchase_price | Float | ราคาที่ซื้อจริง |
| purchase_date | Date | วันที่ซื้อ |
| transport_cost | Float | ค่าขนส่ง |
| dismantling_cost | Float | ค่า outsource รื้อถอน |
| other_cost | Float | ค่าใช้จ่ายอื่น |
| total_cost | Float (computed) | Σ ทุก cost |
| analytic_account_id | Many2one account.analytic.account | สร้างอัตโนมัติ 1 คัน = 1 analytic |
| product_id | Many2one product.product | ตัวซากรถเป็น product (ใช้กับ Unbuild) |
| state | Selection | draft/submitted/approved/purchasing/stocked/completed |
| image_ids | One2many itx.revival.acquired.image | รูปถ่ายซากรถ |
| dismantling_id | Many2one itx.revival.dismantling | ผูกกับ DOC 3 |
| actual_revenue | Float (computed) | Σ ราคาขายจริงอะไหล่ที่ขายแล้ว |
| actual_profit | Float (computed) | actual_revenue - total_cost |
| actual_roi | Float (computed) | actual_profit / total_cost × 100 |
| sold_percentage | Float (computed) | จำนวนชิ้นขาย / ทั้งหมด × 100 |
| note | Text | หมายเหตุ |

### Buttons / Actions
- `action_submit` — draft → submitted (trigger approval workflow)
- `action_create_po` — สร้าง Purchase Order
- `action_confirm_stock` — ยืนยันรับเข้าสต็อก (stocked)
- `action_create_dismantling` — สร้าง DOC 3 (เมื่อ decision = dismantle และ stocked)
- `action_complete` — ปิด cycle

### Analytic Account
สร้างอัตโนมัติตอน create acquired:
```
ชื่อ: "ACQ/2026/0001 - Honda Civic FD 2009"
ทุก transaction ผูก analytic นี้:
  PO (ซื้อรถ)          → debit
  ค่าขนส่ง             → debit
  ค่า outsource        → debit
  ขายอะไหล่            → credit
→ ดู P&L ต่อซากรถแต่ละคันได้ทันที
```

---

## 8. itx.revival.acquired.image

| Field | Type | คำอธิบาย |
|---|---|---|
| acquired_id | Many2one itx.revival.acquired | รถที่ถ่าย |
| image | Image | รูปภาพ |
| description | Char | "ห้องเครื่อง", "หน้าซ้าย" ฯลฯ |
| sequence | Integer | ลำดับ |

---

## 9. DOC 3: itx.revival.dismantling

### Purpose
เอกสารแตกชิ้นส่วน — copy lines จาก assessment พร้อม 6 columns
เมื่อ done: stock_out ซากรถ, stock_in อะไหล่ทุกชิ้น

### States
```
draft → submitted → approved → in_progress → done
              │
           rejected → draft (แก้แล้วส่งใหม่)
```

### Approval
ใช้ `approval.mixin` จาก dynamic_approval_workflow

### Fields (Header)

| Field | Type | คำอธิบาย |
|---|---|---|
| name | Char (sequence) | DIS/2026/0001 |
| acquired_id | Many2one itx.revival.acquired (required) | รถที่จะแตก |
| assessment_id | related acquired.assessment_id store=True | แบบประเมินต้นทาง |
| spec_id | related store=True | สเปครถ |
| dismantling_date | Date | วันที่แตกจริง |
| technician_id | Many2one res.partner | ช่างที่รื้อ |
| outsource_vendor_id | Many2one res.partner | vendor outsource (ถ้ามี) |
| outsource_cost | Float | ค่า outsource จริง |
| bom_id | Many2one mrp.bom | BOM ที่สร้าง (auto generate) |
| unbuild_id | Many2one mrp.unbuild | Unbuild Order |
| state | Selection | draft/submitted/approved/in_progress/done |
| line_ids | One2many itx.revival.dismantling.line | รายการอะไหล่ |
| note | Text | หมายเหตุ |

### Buttons / Actions
- `action_submit` — draft → submitted (trigger approval)
- `action_generate_bom` — สร้าง mrp.bom จาก lines (is_found=True)
- `action_start` — approved → in_progress
- `action_done` — in_progress → done
  → stock_out acquired car product -1
  → stock_in ทุก line (actual_origin, actual_condition) +1
  → สร้าง product ใหม่ถ้ายังไม่มี (actual_origin + actual_condition)

---

## 10. itx.revival.dismantling.line

### Purpose
รายการอะไหล่ใน Dismantling — copy จาก assessment.line
มี 6 columns หลัก: assessed (3 readonly) + actual (3 user กรอก)

| Field | Type | คำอธิบาย |
|---|---|---|
| dismantling_id | Many2one itx.revival.dismantling | หัวเอกสาร |
| sequence | Integer | ลำดับ |
| part_name_id | Many2one itx.info.vehicle.template.part | ชื่ออะไหล่ |
| part_category_id | related | หมวดหมู่ (auto) |
| assessment_line_id | Many2one itx.revival.assessment.line | ต้นทาง |
| **assessed_origin** | Selection (readonly) | origin จาก assessment |
| **assessed_condition** | Selection (readonly) | condition จาก assessment |
| **assessed_est_price** | Float (readonly) | ราคาคาดการณ์จาก assessment |
| avg_part_cost | Float (readonly) | ต้นทุนที่ allocate จาก assessment |
| **actual_origin** | Selection | origin จริงที่รื้อออกมาได้ |
| **actual_condition** | Selection | condition จริง |
| **actual_sale_price** | Float | ราคาขายที่ตั้ง (จริง) |
| product_id | Many2one product.template | product สำหรับ stock_in |
| is_included | Boolean | รวมใน Unbuild หรือไม่ (default: True) |
| note | Char | หมายเหตุ |

### หมายเหตุ product_id ใน dismantling_line
เมื่อ action_done:
- lookup product.template ด้วย key: spec_id + part_name_id + actual_origin + actual_condition
- พบ → ใช้ id นั้น
- ไม่พบ → สร้างใหม่อัตโนมัติ (auto internal reference จาก itx_info_vehicle)

---

## 11. Generate Assessment Lines Logic (action_generate_lines)

```
Input:
  assessment.spec_id      → รู้ generation → รู้ body_type_id
  assessment.body_type_id → KEY

Process:
  Step 1: ดึง itx.info.vehicle.template.bom
          WHERE body_type_id = assessment.body_type_id
          ORDER BY sequence
          → ได้ list of template_part ~54 ชิ้น

  Step 2: For each template_part:
          Lookup product.template WHERE:
            itx_spec_id      = assessment.spec_id
            itx_part_name_id = template_part.id
            itx_part_origin  = 'oem'    ← default
            itx_condition    = 'fair'   ← default
          
          ถ้าพบ  → ใช้ product.id นั้น
          ไม่พบ  → สร้าง product.template ใหม่
                    (auto internal reference ทำงานเองจาก itx_info_vehicle)
                    → ใช้ id ใหม่

  Step 3: สร้าง assessment.line ทุกชิ้น
          origin    = 'oem'   (default, user แก้ได้)
          condition = 'fair'  (default, user แก้ได้)
          cost_weight = 100 / จำนวน parts (เฉลี่ย)
          is_found  = True    (default, สายสืบ untick ถ้าไม่เจอ)

Output:
  assessment.line_ids ครบทุกชิ้น พร้อม product_id
```

---

## 12. Generate BOM Logic (action_generate_bom ใน Dismantling)

```
Input:
  dismantling.acquired_id → assessment → lines (is_found=True)

Process:
  Step 1: สร้าง mrp.bom
          product_id = acquired.product_id (ตัวซากรถ)
          type       = 'normal'
          itx_acquired_id = acquired.id

  Step 2: For each dismantling.line WHERE is_included = True:
          สร้าง mrp.bom.line
            product_id        = line.product_id
            product_qty       = 1
            itx_cost_weight   = line assessment cost_weight
            itx_expected_price = line.assessed_est_price

  Step 3: ผูก bom_id กลับที่ dismantling และ acquired

Output:
  mrp.bom + lines พร้อม Unbuild
```

---

## 13. Inherit Models

### mrp.bom (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_acquired_id | Many2one itx.revival.acquired | ผูกกับรถคันไหน |

### mrp.bom.line (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_cost_weight | Float | % สัดส่วนต้นทุน |
| itx_allocated_cost | Float (computed) | total_cost × weight / Σweight |
| itx_expected_price | Float | ราคาขายคาดการณ์ |

### mrp.unbuild (inherit)
| Field เพิ่ม | Type | คำอธิบาย |
|---|---|---|
| itx_acquired_id | Many2one itx.revival.acquired | ผูกกับรถคันไหน |
| itx_dismantling_id | Many2one itx.revival.dismantling | ผูกกับ Dismantling |

---

## 14. Sequences ที่ต้องสร้าง

```
ASM/%(year)s/%(seq)05d  → itx.revival.assessment
ACQ/%(year)s/%(seq)05d  → itx.revival.acquired
DIS/%(year)s/%(seq)05d  → itx.revival.dismantling
```

---

## 15. โครงสร้าง Module

```
itx_revival_vehicle/
├── __manifest__.py
│
├── models/
│   ├── __init__.py
│   ├── itx_revival_assessment.py
│   ├── itx_revival_assessment_line.py
│   ├── itx_revival_acquired.py
│   ├── itx_revival_acquired_image.py
│   ├── itx_revival_dismantling.py
│   ├── itx_revival_dismantling_line.py
│   ├── mrp_bom.py                        (inherit)
│   ├── mrp_bom_line.py                   (inherit)
│   └── mrp_unbuild.py                    (inherit)
│
├── views/
│   ├── itx_revival_assessment_views.xml
│   ├── itx_revival_acquired_views.xml
│   ├── itx_revival_dismantling_views.xml
│   └── menuitems.xml
│
├── report/
│   └── itx_revival_checklist_report.xml  (PDF checklist สายสืบ)
│
├── security/
│   └── ir.model.access.csv
│
└── data/
    └── ir_sequence_data.xml
```

---

## 16. Menu Structure

```
Revival Vehicle (main menu)
├── Assessments              ← itx.revival.assessment
├── Acquired Vehicles        ← itx.revival.acquired
├── Dismantling Orders       ← itx.revival.dismantling
└── Reports
    └── ROI by Vehicle       ← computed/SQL view
```

---

## 17. PDF Checklist (สำหรับสายสืบ)

ต้องมีข้อมูลต่อไปนี้:
```
Header:
  - ASM number, spec, body_type, location
  - asking_price, target_price, expected_revenue, expected_roi

Lines (table):
  - ลำดับ
  - ชื่ออะไหล่ (ภาษาไทย)
  - ชื่ออะไหล่ (English)
  - origin (default)
  - condition (default)
  - ราคาคาดการณ์
  - [ ] is_found (checkbox)
  - actual_condition (dropdown/blank)
  - หมายเหตุ (blank)
```

---

## 18. Security Groups

```
revival.group_revival_manager   ← เข้าถึงได้ทุกอย่าง รวม config
revival.group_revival_user      ← ใช้งานทั่วไป ไม่เข้า config
```

---

## 19. สิ่งที่ต้องตรวจสอบก่อนเริ่ม (Prerequisite Check)

```
1. itx_info_vehicle v19.0.1.4.4 ติดตั้งแล้ว
   ✓ template_part (~79 records)
   ✓ template_bom (~378 records)
   ✓ product.template UK: spec + part_name + origin + condition

2. itx.vehicle.generation มี body_type_id field หรือไม่?
   → ถ้าไม่มี ต้องเพิ่มใน itx_info_vehicle ก่อน
   → เพราะ assessment ต้องใช้ body_type เพื่อ lookup template.bom

3. dynamic_approval_workflow ติดตั้งแล้ว
   → ตรวจสอบ approval.mixin มีใน system

4. Odoo version: 19.0 Community Edition
```

---

## 20. Key Design Decisions (สรุปการตัดสินใจสำคัญ)

```
1. ไม่มี ItxDismantlingLine แยก
   → ใช้ assessment.line + dismantling.line แทน
   → BOM generate จาก dismantling.line (is_included=True)

2. product.template สร้างอัตโนมัติตอน generate_lines
   → key: spec + part_name + origin + condition
   → ถ้ายังไม่มีสร้างใหม่ auto (UK ของ itx_info_vehicle รับประกัน)

3. cost_weight เริ่มต้นเฉลี่ยเท่ากัน (100/n)
   → user แก้ได้ใน assessment.line
   → TODO: ถาม user ว่าต้องการ weight จาก market price ด้วยหรือไม่

4. Approval ใช้ dynamic_approval_workflow
   → inherit approval.mixin ทั้ง 3 docs
   → DP config approver เองจาก UI ได้เลย

5. 1 Acquired Vehicle = 1 Analytic Account
   → สร้างอัตโนมัติตอน create acquired
   → ติดตาม P&L ต่อซากรถแต่ละคัน

6. dismantling.line มี assessed_XXX (readonly) + actual_XXX (editable)
   → assessed_XXX copy มาจาก assessment.line ตอนสร้าง dismantling
   → actual_XXX user กรอกตอนรื้อจริง
   → stock_in ใช้ actual_origin + actual_condition เป็น key lookup/create product

7. is_found default = True
   → สายสืบ untick ถ้าไม่เจอ (ง่ายกว่า tick ทีละชิ้น)

8. Platform model ยังไม่ implement
   → เพิ่มทีหลังได้ (แค่ Many2one ใน generation)
   → DP ยังไม่เข้าใจ concept Platform
```
