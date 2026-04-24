# Blueprint: As-Is & To-Be
# ระบบจัดการซากรถ — ITX Revival Vehicle
## DP Survey & Law Co., Ltd. (ทิพยประกันภัย)

**Document:** Blueprint As-Is & To-Be  
**Version:** 1.0  
**Date:** 2026-04-14  
**Prepared by:** IT Expert Training & Outsourcing Co.  
**Module:** `itx_revival_vehicle` (Odoo 19)  
**Source:** เอกสารการทำงานส่งให้ทีม odoo ver2.pdf, workflow_final_001.md, gap_analysis_vs_client_requirements.md

---

## สารบัญ

1. [Executive Summary](#1-executive-summary)
2. [As-Is: สภาพปัจจุบัน (ก่อนใช้ระบบ)](#2-as-is-สภาพปัจจุบัน)
3. [To-Be: ระบบใหม่ใน Odoo 19](#3-to-be-ระบบใหม่ใน-odoo-19)
4. [Feature Matrix: As-Is vs To-Be](#4-feature-matrix)
5. [Workflow Comparison](#5-workflow-comparison)
6. [Module Breakdown & Scope](#6-module-breakdown--scope)
7. [Integration Points](#7-integration-points)
8. [Reports & Documents](#8-reports--documents)
9. [Open Questions for User](#9-open-questions-for-user)
10. [Risk & Assumptions](#10-risk--assumptions)
11. [Implementation Phases](#11-implementation-phases)

---

## 1. Executive Summary

### วัตถุประสงค์โครงการ

พัฒนาระบบ ERP บน Odoo 19 เพื่อจัดการวงจรชีวิตซากรถครบวงจร ตั้งแต่รับรายการจากบริษัทประกัน → ประเมิน → ตัดสินใจ → ซื้อ/ขาย → รื้อถอน → ขายอะไหล่ → ชำระค่าซาก → ปิดงาน  

ทดแทนกระบวนการทำงานแบบ manual ที่ใช้ Excel, กระดาษ, email, และ LINE กลุ่มเป็นหลัก

### ขอบเขตงาน

| หมวด | ขอบเขต |
|---|---|
| Business Unit | DP Survey & Law Co., Ltd. |
| Supplier หลัก | ทิพยประกันภัย (มจ.) |
| ปริมาณงาน | ~15-20 คัน/สัปดาห์ |
| เส้นทางธุรกิจ | (A) ขายยกคัน (Broker), (B) แยกอะไหล่ (Inventory) |
| Platform | Odoo 19 Community + Custom Modules |

---

## 2. As-Is: สภาพปัจจุบัน

### 2.1 ภาพรวมกระบวนการปัจจุบัน (Manual)

DP Survey & Law ทำธุรกิจซื้อ-ขายซากรถจากบริษัทประกันภัย โดยกระบวนการทั้งหมดในปัจจุบัน**ทำด้วยมือ** ผ่าน email, Excel, กระดาษ, และ LINE กลุ่ม

### 2.2 As-Is Flow: ขายซากอะไหล่ (เส้นทาง B)

```
PDF ข้อ 1-10 (ขั้นตอนการทำงานจัดอะไหล่):
```

| ขั้นตอน | กระบวนการปัจจุบัน | เครื่องมือ | ปัญหา/จุดอ่อน |
|---|---|---|---|
| 1. รับออเดอร์ | รับรายการสั่งอะไหล่จากบริษัทประกัน ผ่านระบบ ePart (BlueVenture/EMCS) | ePart web portal | ต้อง login ระบบภายนอก, ไม่เชื่อมกับระบบภายใน |
| 2. หาสินค้า | ติดต่อร้านอะไหล่ ส่งรายการให้เสนอราคา | LINE กลุ่ม, โทรศัพท์ | ไม่มี database ร้านอะไหล่, ราคาไม่มี history |
| 3. เสนอราคา | ร้านอะไหล่เสนอราคากลับมา เลือกร้านที่ (1) เสนอเร็ว (2) ราคาถูกกว่า | LINE, ใบรายการอะไหล่ (กระดาษ) | เปรียบเทียบราคาด้วยมือ, ไม่มี audit trail |
| 4. DP กรอกราคา | นำราคาจากร้านอะไหล่ กรอกเสนอในระบบ ePart | ePart web portal | manual data entry ซ้ำซ้อน |
| 5. ได้อนุมัติ | ประกันอนุมัติ → DP confirm order ไปร้านอะไหล่ | LINE กลุ่ม | ไม่มี PO อิเล็กทรอนิกส์ |
| 6. ร้านจัดส่ง | ร้านอะไหล่จัดส่งทั่วประเทศ (กทม. ฟรี / ต่างจังหวัดมีค่าขนส่ง) SLA ≤3 วันทำการ | ขนส่ง | ไม่มีระบบ track การจัดส่ง |
| 7. ลูกค้าเซ็นรับ | อู่เซ็นรับสินค้า → ร้านอะไหล่นำใบส่งของเข้าระบบ ePart | กระดาษ + ePart | หลายขั้นตอน, delay |
| 8. วางบิล | DP ตรวจสอบ ใบแจ้งหนี้/ใบเสร็จ/ใบกำกับ ตรงกัน 3 ชุด → กดวางบิลใน ePart | ePart + เอกสารกระดาษ | reconcile ด้วยมือ |
| 9. จ่ายเงินร้าน | DP จ่ายเงินร้านอะไหล่ (ใบส่งของ + ใบแจ้งหนี้/เสร็จ/กำกับ) → โอนผ่านธนาคาร | ธนาคาร | ไม่เชื่อมกับบัญชี |
| 10. เบิกเงินทิพย | ทำใบเบิก ePart + ใบแจ้งหนี้/เสร็จ/กำกับ + ใบอนุมัติสั่งอะไหล่ → รวมส่ง ทิพยฯ วางบิลทุกวันจันทร์ | ePart + E-Billing | batch process สัปดาห์ละครั้ง |

### 2.3 As-Is Flow: ขายซากรถยกคัน (เส้นทาง A)

```
PDF ข้อ 1-9 (ขั้นตอนงานขายซากอะไหล่ — ทิพยประกันภัย):
```

| ขั้นตอน | กระบวนการปัจจุบัน | เครื่องมือ | ปัญหา/จุดอ่อน |
|---|---|---|---|
| 1. รับรายการซาก | ได้รับรายการซากจากทิพยฯ ทาง email สัปดาห์ละครั้ง ~15-20 คัน | email (Excel/PDF) | ไม่มี batch import, กรอกมือ |
| 2. ตรวจสอบข้อมูลรถ | นำ ECF เข้าระบบทิพยฯ ดูสภาพรถ ลักษณะการชน รูปจากศูนย์/อู่ | ECF web portal | login ระบบภายนอก, copy-paste ข้อมูล |
| 3. ประเมินและตัดสินใจ | เจ้าหน้าที่ดูรูปจากระบบศูนย์ → ตัดสินใจ: ขายยกคัน / ชำแหละ / ไม่ซื้อ **ชีวิตจริง: ต้องถ่ายรูปหน้างาน + อัพโหลดเข้าระบบด้วย** | ตาเปล่า + ฟอร์มกระดาษ (Checklist 20 ช่อง) | ไม่มี digital checklist, รูปกระจัดกระจาย |
| 4. เสนอราคาซื้อซาก | ส่ง email เสนอราคา = % ของทุนประกัน (แจ้งจอด 15% / ไม่แจ้งจอด 25%) | email + คำนวณมือ | สูตรอยู่ในหัว ไม่มี auto-calculate |
| 5. หาลูกค้า/เจรจาขาย | ประกาศขายผ่าน LINE กลุ่ม (ยี่ห้อ ปี ทะเบียน สถานที่จอด + ราคา) | LINE กลุ่ม | ไม่มี CRM, ไม่ track เจรจา |
| 6. รับชำระเงิน | ลูกค้าจ่ายมัดจำ 5,000 บาท → ออกใบเสร็จมัดจำ → จ่ายครบ → ทำ ใบสั่งขาย | กระดาษ + Excel | ไม่มี payment tracking, ไม่มี partial payment |
| 7. ขอใบปล่อยรถ | เมื่อเงินครบ → ส่งใบสั่งขายให้การเงิน → ตรวจสอบ slip → ขอใบปล่อยจากทิพยฯ | email + กระดาษ | manual process, ช้า |
| 8. แจ้งผลทิพยฯ | ตอบ email ทิพยฯ ว่าซื้อคันไหน (เช่น 7 คัน ตกลง 3 คืน 4) **เงื่อนไข: ซื้อได้ก็ต่อเมื่อลูกค้าจ่ายครบ** | email | ไม่มี batch workflow |
| 9. ปิดงาน | โอนค่าซากให้ทิพยฯ → รอรับเล่มทะเบียน → โอนกรรมสิทธิ์ (ถ้าทำ) | ธนาคาร + กรมขนส่ง | ไม่ track สถานะโอนกรรมสิทธิ์ |

### 2.4 As-Is Flow: แยกอะไหล่ (เส้นทาง B เมื่อ DP ตัดสินใจซื้อเอง)

| ขั้นตอน | กระบวนการปัจจุบัน | เครื่องมือ | ปัญหา/จุดอ่อน |
|---|---|---|---|
| 5. ขอใบปล่อยรถ | ขอใบปล่อยจากทิพยฯ | email | เหมือนเส้นทาง A |
| 6. ประสานทีมช่าง | ยกรถไปเก็บที่อู่/โกดัง → ทีมช่างรื้อ → ลงข้อมูลเก็บอะไหล่เข้า stock | กระดาษ + Excel | ไม่มี WMS, inventory ไม่ real-time |
| 7. ลูกค้ามาซื้อ | เสนอขายผ่าน LINE กลุ่ม / ลูกค้า walk-in | LINE, โทร | ไม่มี eCommerce |
| 8. ชำระเงิน | ลูกค้าจ่ายเงิน → ออก SO + ใบเสร็จ + ใบกำกับภาษี | กระดาษ + Excel | ไม่มี POS/SO อิเล็กทรอนิกส์ |
| 9. QC + จัดส่ง | ตรวจสอบอะไหล่ → ออกใบจัดส่ง → ส่ง | กระดาษ | ไม่มี QC workflow |
| 10. ลูกค้าเซ็นรับ | ลูกค้าเซ็นรับ = ปิดงาน | กระดาษ | ไม่มี digital signature |
| **ชำระค่าซาก** | สามารถทำก่อนหรือหลังปิดงานขายได้ | ธนาคาร | ไม่ block การขาย |

### 2.5 เอกสารที่ใช้ในปัจจุบัน (กระดาษ)

| เอกสาร | ใช้ตอนไหน | รายละเอียด |
|---|---|---|
| **ใบประเมินซากรถ** (Checklist) | ขั้นตอน 3 | ฟอร์ม 20 ช่อง: ยี่ห้อ รุ่น ปี ทะเบียน สี ไมล์ สถานที่จอด, สภาพดี/พอใช้, checkbox มาซื้อ/ไม่ซื้อ |
| **ใบแจ้งหนี้/ใบกำกับภาษี** (Invoice/Tax Invoice) | ขายอะไหล่ | SIT-format, DP ออกให้ลูกค้า: product code (ATP-300-TIP), เลขเคลม, เลขตัวถัง, ยี่ห้อ/รุ่น, ทะเบียน, VAT 7%, credit term 30 วัน |
| **ใบรายการอะไหล่** | สั่งของจากร้าน | รายการ part + ราคา + จำนวน + ลายเซ็นร้าน |
| **แบบขออนุมัติจ่าย** (DP-AC-005) | ก่อนโอนค่าซากให้ทิพยฯ | รายการรถ + ราคา + ส่วนลด% + VAT 7% + ลงนาม 4 ตำแหน่ง (ผู้จัดทำ, ผู้ตรวจสอบ, ผู้อนุมัติซื้อ, ผู้อนุมัติ) |
| **ใบส่งสินค้าชั่วคราว** (Delivery Note) | จัดส่งอะไหล่ | product code, รายการ, จำนวน, ราคา, ส่วนลด%, ลายเซ็นผู้รับ |

### 2.6 ระบบภายนอกที่ใช้

| ระบบ | เจ้าของ | DP ใช้ทำอะไร |
|---|---|---|
| **ePart** (BlueVenture) | BlueVenture Group | รับ order อะไหล่จากประกัน, เสนอราคา, confirm, วางบิล |
| **EMCS** (Electronic Motor Claim Solution) | BlueVenture Group | ดูข้อมูลเคลม, สภาพรถ, ค้นหา ECF |
| **E-Billing** | BlueVenture / ทิพยฯ | ส่งใบเบิกเงินจากทิพยฯ |
| **LINE กลุ่ม** | — | เจรจาขาย, ส่งรูป, confirm order กับร้านอะไหล่ |
| **Excel** | — | จัดการ stock, ราคา, รายงาน |

---

## 3. To-Be: ระบบใหม่ใน Odoo 19

### 3.1 Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                    Odoo 19 ERP Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────┐  ┌──────────────────┐  ┌────────────────┐ │
│  │  itx_info_vehicle │  │itx_revival_vehicle│  │  Odoo Standard │ │
│  │  (Master Data)    │  │  (Lifecycle)      │  │  Modules       │ │
│  │                   │  │                   │  │                │ │
│  │  - Brand/Model    │  │  - Assessment     │  │  - Purchase    │ │
│  │  - Spec/Gen       │  │  - Acquired       │  │  - Sale        │ │
│  │  - Body Type      │  │  - Dismantling    │  │  - MRP/Unbuild │ │
│  │  - Part Template  │  │  - Images         │  │  - Stock/WMS   │ │
│  │  - Part Category  │  │                   │  │  - Account     │ │
│  │  - Origin         │  │                   │  │  - Analytic    │ │
│  │  - Condition      │  │                   │  │                │ │
│  │  - BOM Template   │  │                   │  │                │ │
│  └──────────────────┘  └──────────────────┘  └────────────────┘ │
│                                                                  │
│  Product Variants (Dynamic: Origin × Condition per Part+Spec)    │
│  Stock Lots (VIN-based tracking per part per vehicle)            │
│  Analytic Accounts (1 vehicle = 1 cost center)                   │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 To-Be Flow: Assessment (ท่อน 1 — Decision Phase)

**Model:** `itx.revival.assessment`  
**States:** `draft → assessed → offering → returned / sold / dismantle`

| ขั้นตอน | ระบบใหม่ | As-Is เทียบ | สิ่งที่เปลี่ยน |
|---|---|---|---|
| 1. รับรายการซาก | สร้าง Assessment record, กรอก spec, ECF, ทุนประกัน, แจ้งจอด/ไม่แจ้งจอด | email → Excel → กรอกมือ | Digital record + auto sequence |
| 2. ดูสภาพรถ | เลือก spec → Generate Lines จาก BOM Template อัตโนมัติ (อะไหล่ทุกชิ้นตาม body type) | ดูรูปจากระบบศูนย์ + กรอก checklist กระดาษ | BOM-driven parts list |
| 3. Field survey | อัพโหลดรูป (exterior/interior/engine/damage/document) + กรอก is_found, qty, สภาพ per line | ถ่ายรูป + กรอกกระดาษ | Digital image + per-part assessment |
| 4. คำนวณราคา | `suggested_price` = ทุนประกัน × % (configurable via Settings) + expected revenue/profit/ROI auto-compute | คำนวณมือ/ในหัว | Auto-calculate + configurable % |
| 5. ตัดสินใจ | 3 ปุ่ม: Return (ไม่ซื้อ), Dismantle (แยกอะไหล่), Offer (ขายยกคัน) | พิมพ์ checklist + เซ็น มาซื้อ/ไม่ซื้อ | One-click decision |
| 6. Offering (ถ้าขายยกคัน) | Wait state มี deadline, กรอก buyer + ราคาขาย, ระบบแจ้งเตือนหมดเวลา | ประกาศ LINE + รอ + จำเอง | Digital deadline tracking |
| 7. สร้าง Acquired | ปุ่ม "Create Acquired" → สร้าง record + analytic account อัตโนมัติ | — | New workflow step |

### 3.3 To-Be Flow: Acquired — Path A (ขายยกคัน / Broker Model)

**Model:** `itx.revival.acquired` (decision = `sell_whole`)  
**States:** `draft → po_created → releasing → delivered → settling → closed`

| ขั้นตอน | ระบบใหม่ | As-Is เทียบ | สิ่งที่เปลี่ยน |
|---|---|---|---|
| 1. สร้าง PO | ปุ่ม Create PO → auto PO + analytic distribution | — (ไม่มี PO) | Purchase Order อิเล็กทรอนิกส์ |
| 2. ขอใบปล่อย | ปุ่ม Request Release → บันทึก release_request_date | ส่ง email ขอ | Digital tracking |
| 3. ลูกค้ารับรถ | ปุ่ม Delivered → delivery_date (Dropship — ไม่เข้า stock DP) | ส่งมอบ + กระดาษ | Dropship route |
| 4. ชำระค่าซาก | ปุ่ม Settle → กรอก payment date/amount + reg. book received | โอนเงิน + กระดาษ | Digital settlement tracking |
| 5. ปิดงาน | ปุ่ม Close → ownership transfer tracking | — | Complete lifecycle |

### 3.4 To-Be Flow: Acquired — Path B (แยกอะไหล่ / Inventory Model)

**Model:** `itx.revival.acquired` (decision = `dismantle`)  
**States:** `draft → po_created → releasing → stocked → dismantling → parts_ready → settling → closed`

| ขั้นตอน | ระบบใหม่ | As-Is เทียบ | สิ่งที่เปลี่ยน |
|---|---|---|---|
| 1. สร้าง PO | ปุ่ม Create PO → auto PO + vehicle product | — | Purchase Order |
| 2. ขอใบปล่อย | ปุ่ม Request Release | email | Digital tracking |
| 3. รับเข้าโกดัง | ปุ่ม Confirm Stock → PO Receipt + VIN Lot creation อัตโนมัติ | ลง Excel | Odoo Stock + lot tracking |
| 4. รื้อถอน | สร้าง Dismantling Order → Generate Lines จาก Assessment → Start → Unbuild Order | ทีมช่างลงมือ + กรอก Excel | MRP Unbuild + per-part lot |
| 5. Done | ปุ่ม Done → stock.move per part: Production → WH/Stock (per-part destination by category) → VIN lot per part | ลงข้อมูลเข้า Excel | Automated stock moves + lot traceability |
| 6. ขายอะไหล่ | Standard Odoo SO → Invoice → Delivery (with lot tracking) | LINE + กระดาษ + ePart | Full SO/Invoice/Delivery cycle |
| 7. ชำระค่าซาก | ปุ่ม Settle (ไม่ block การขาย parts) | โอนเงิน เมื่อไรก็ได้ | Digital tracking, non-blocking |
| 8. ปิดงาน | ปุ่ม Close | — | Complete lifecycle |

### 3.5 Key Automations

| Automation | รายละเอียด | ทดแทนงาน Manual |
|---|---|---|
| **BOM Template → Assessment Lines** | เลือก Spec → body type → auto generate list อะไหล่ทุกชิ้นตาม template | กรอก checklist 20 ช่องด้วยมือ |
| **Suggested Price** | ทุนประกัน × % (configurable) | คำนวณในหัว |
| **Expected ROI** | Σ(expected_price × qty) ÷ target_price | ไม่มี |
| **VIN Lot Creation** | Confirm Stock → auto create stock.lot(VIN) | ไม่มี lot tracking |
| **Unbuild → Stock Moves** | Dismantling Done → 1 consume move + N produce moves with VIN lot per part | ลง Excel |
| **Per-Part Destination** | template_part → category → warehouse stock location | ไม่มี |
| **Analytic Account** | 1 Acquired = 1 analytic account (auto-create) | ไม่มี cost tracking per vehicle |
| **Dynamic Variants** | Origin × Condition → product.product variant (auto-create) | ไม่แยก variant |
| **Offering Deadline** | Compute `is_offering_expired` + search filter | จำเอง |

---

## 4. Feature Matrix

### 4.1 Assessment Features

| Feature | As-Is | To-Be (Implemented) | To-Be (Planned) | Status |
|---|---|---|---|---|
| Vehicle Spec selection | ✗ | ✓ spec_id → auto brand/model/gen | — | Done |
| ECF Claim Number | ✗ | ✓ ecf_claim_number (indexed) | — | Done |
| Insurance Value | ✗ | ✓ insurance_value (monetary) | — | Done |
| แจ้งจอด/ไม่แจ้งจอด | ✗ | ✓ is_parking_reported | — | Done |
| Suggested Price (auto) | ✗ | ✓ computed from insurance_value × % | — | Done |
| Configurable % | ✗ | ✓ ir.config_parameter | — | Done |
| Plate Number | ✗ | ✓ plate_number + plate_province | — | Done |
| Registration Book Status | ✗ | ✓ selection (clean/stamped/lost/unknown) | — | Done |
| Claim Date | ✗ | ✓ claim_date | — | Done |
| BOM-driven Parts List | ✗ | ✓ Generate Lines from spec BOM | — | Done |
| Per-part assessment | ✓ (กระดาษ) | ✓ is_found, qty, origin, condition | — | Done |
| Field Survey Images | ✓ (กระดาษ/รูปกระจาย) | ✓ image_ids with category | — | Done |
| Expected Revenue/ROI | ✗ | ✓ computed per assessment | — | Done |
| Offering Wait State | ✗ | ✓ state=offering, deadline, expired filter | — | Done |
| Decision Workflow | ✓ (checkbox กระดาษ) | ✓ 3-way: return/dismantle/offer | — | Done |
| Batch Import (15-20 คัน) | ✗ email → กรอกมือ | — | ✓ Import wizard/CSV | Planned |
| Print Checklist (PDF) | ✓ (กระดาษเปล่า) | — | ✓ QWeb report | Planned |
| Overall Condition (field survey) | ✓ (กระดาษ) | ✓ overall_condition + note | — | Done |

### 4.2 Acquired Features

| Feature | As-Is | To-Be (Implemented) | To-Be (Planned) | Status |
|---|---|---|---|---|
| Purchase Order | ✗ | ✓ auto PO creation | — | Done |
| VIN Lot Tracking | ✗ | ✓ stock.lot with VIN | — | Done |
| Release Document Tracking | ✗ | ✓ release_request_date, doc_date | — | Done |
| Settlement Tracking | ✗ | ✓ payment date/amount, reg book, ownership transfer | — | Done |
| Analytic Account per Vehicle | ✗ | ✓ auto-create analytic | — | Done |
| Path A: Broker/Dropship | ✗ | ✓ state flow (sold→releasing→delivered→settling→closed) | ✓ SO creation, Dropship route | Partial |
| Path B: Inventory/Dismantle | ✗ | ✓ full flow (po→stock→unbuild→parts_ready→closed) | — | Done |
| ROI Analysis | ✗ | ✓ actual_revenue, profit, roi, sold_% | ✓ Compute from actual SO | Partial |
| Deposit Tracking (5,000 บาท) | ✗ | — | ✓ sale.advance.payment.inv | Planned |
| SO for sell_whole | ✗ | ✓ field exists | ✓ Auto SO + Dropship | Planned |

### 4.3 Dismantling Features

| Feature | As-Is | To-Be (Implemented) | To-Be (Planned) | Status |
|---|---|---|---|---|
| Dismantling Order | ✗ | ✓ itx.revival.dismantling | — | Done |
| Generate Lines from Assessment | ✗ | ✓ action_generate_lines | — | Done |
| Unbuild Order (MRP) | ✗ | ✓ auto-create mrp.unbuild | — | Done |
| Stock Moves (direct) | ✗ | ✓ consume + produce moves with VIN lot | — | Done |
| Per-part Variant Resolution | ✗ | ✓ actual vs assessed origin/condition | — | Done |
| Per-part Destination | ✗ | ✓ template_part → category → warehouse | — | Done |
| Technician Tracking | ✗ | ✓ technician_id | — | Done |

### 4.4 Reports & Documents

| Document | As-Is | To-Be Status | Notes |
|---|---|---|---|
| ใบประเมินซากรถ (Checklist) | กระดาษ 20 ช่อง | Planned | QWeb report from assessment lines |
| ใบแจ้งหนี้/ใบกำกับภาษี | DP ออกเอง (SIT format) | Planned | Customize Odoo invoice template |
| แบบขออนุมัติจ่าย (DP-AC-005) | กระดาษ 4 ลงนาม | Planned | QWeb report + PO approval |
| ใบส่งสินค้าชั่วคราว (Delivery Note) | กระดาษ | Planned | Customize Odoo delivery slip |
| ใบรายการอะไหล่ | กระดาษ | Planned | QWeb report from dismantling lines |

---

## 5. Workflow Comparison

### 5.1 State Machine Summary

**Assessment (ท่อน 1):**
```
As-Is:  ดูรูป → กรอก checklist → checkbox ซื้อ/ไม่ซื้อ → จบ
To-Be:  draft ─→ assessed ─→ offering ─┬→ returned (END)
                    │                    ├→ sold ─→ Create Acquired
                    │                    └→ dismantle ─→ Create Acquired
                    ├→ returned (END)
                    └→ dismantle ─→ Create Acquired
```

**Acquired (ท่อน 2):**
```
As-Is:  ไม่มีระบบ (email + กระดาษ)
To-Be:  draft → po_created → releasing ─┬→ stocked → dismantling → parts_ready ─┐
                                         │                                        │
                                         └→ delivered ─────────────────────────────┤
                                                                                   │
                                                                                   └→ settling → closed
```

### 5.2 Key Design Decisions

| Decision | Rationale |
|---|---|
| **Broker Model (Path A)** | DP ไม่ซื้อจนกว่าลูกค้าจ่ายครบ → ใช้ Dropship route (SO → auto PO) |
| **Offering = Wait State** | ประกันให้ deadline ~30 วัน → ต้อง track + แจ้งเตือน |
| **Settlement ไม่ block ขาย** | PDF ระบุชัด: ชำระค่าซากทำก่อนหรือหลังขายก็ได้ |
| **1 Vehicle = 1 Analytic** | Track ROI per vehicle (cost center) |
| **Dynamic Variant (Origin × Condition)** | อะไหล่เดียวกัน spec เดียวกัน ต่าง origin/condition = variant ต่างกัน |

---

## 6. Module Breakdown & Scope

### 6.1 Module: `itx_info_vehicle` (Master Data)

| Component | Description | Status |
|---|---|---|
| Vehicle Brand/Model/Generation/Spec | ข้อมูลรถ ยี่ห้อ/รุ่น/รุ่นย่อย/spec | Done |
| Body Type | ประเภทตัวถัง → เชื่อม BOM Template | Done |
| Template Part | master list อะไหล่ per body type | Done |
| Part Category | หมวดหมู่อะไหล่ (ตัวถัง/ไฟฟ้า/เครื่อง/ฯลฯ) | Done |
| Part Origin | แหล่งที่มา (OEM/เทียบ/มือสอง) → product attribute | Done |
| Part Condition | สภาพ (ดี/พอใช้/ชำรุด) → product attribute | Done |
| BOM Template | body type → list of template parts + default origin/condition | Done |

### 6.2 Module: `itx_revival_vehicle` (Lifecycle)

| Component | Description | Status |
|---|---|---|
| Assessment (ท่อน 1) | ประเมินซาก + ตัดสินใจ (6 states, 5 paths) | **Done** |
| Assessment Line | per-part: found/qty/origin/condition/expected_price | Done |
| Assessment Image | รูปถ่าย + category (6 ประเภท) | Done |
| Acquired (ท่อน 2) | ซื้อรถ + manage lifecycle (9 states, 2 paths) | **Done** |
| Dismantling (ท่อน 2) | รื้อถอน + unbuild + stock moves (3 states) | **Done** |
| Dismantling Line | per-part: assessed vs actual + lot tracking | Done |
| Path A: SO + Dropship (ท่อน 3) | สร้าง SO ขายยกคัน + Dropship route | **Planned** |
| Deposit Tracking (ท่อน 3) | มัดจำ 5,000 + partial payment | **Planned** |
| Reports (ท่อน 4) | Checklist, DP-AC-005, Invoice, Delivery Note | **Planned** |
| Batch Import (ท่อน 4) | Import 15-20 คันจาก email/CSV | **Planned** |

### 6.3 Dependencies

```
itx_revival_vehicle
├── itx_info_vehicle     (master data: spec, parts, BOM template)
├── mrp                  (Unbuild Order)
├── purchase_stock       (PO + incoming picking)
└── account              (analytic accounts)

Future:
├── sale_stock           (SO + delivery for Path A & parts sales)
└── sale_management      (quotation → SO for sell_whole)
```

---

## 7. Integration Points

### 7.1 Odoo Standard Module Integration

| Module | Integration | Status |
|---|---|---|
| **Purchase** | PO auto-creation from Acquired | Done |
| **Stock** | VIN lot, stock.move (consume/produce), picking validation | Done |
| **MRP** | Unbuild Order (bypassed validate, direct stock.move) | Done |
| **Account/Analytic** | 1 vehicle = 1 analytic account, PO line distribution | Done |
| **Sale** | SO for sell_whole (Path A) + parts sales | Planned |
| **Product Variants** | Dynamic Origin × Condition via product.attribute | Done |

### 7.2 External System Integration

| ระบบ | Integration ที่ต้องการ | Status | Priority |
|---|---|---|---|
| **ePart / EMCS** (BlueVenture) | รับ order อะไหล่, เสนอราคา, วางบิล | **Not in scope** (Phase 2+) | Low |
| **E-Billing** (ทิพยฯ) | ส่งใบเบิกเงิน | **Not in scope** | Low |
| **LINE กลุ่ม** | ประกาศขาย, confirm order | **Not in scope** | Medium |
| **ECF Portal** | ดึงข้อมูลเคลมอัตโนมัติ | **Not in scope** | Low |

---

## 8. Reports & Documents

### 8.1 Reports ที่ต้องสร้าง

| Report | Source Model | Key Fields | Template Reference (PDF) | Status |
|---|---|---|---|---|
| **ใบประเมินซากรถ** (Checklist) | assessment + assessment.line | ยี่ห้อ, รุ่น, ปี, ทะเบียน, สถานที่, สี, ไมล์, 20 ช่อง part, สภาพดี/พอใช้ | PDF p.8 (ฟอร์ม Checklist) | Planned |
| **แบบขออนุมัติจ่าย** (DP-AC-005) | acquired (batch) | รายการรถ + ราคา + ส่วนลด% + VAT 7%, ลงนาม 4 ตำแหน่ง | PDF p.9 (DP-AC-005 form) | Planned |
| **ใบแจ้งหนี้/ใบกำกับภาษี** | account.move (invoice) | product code, เลขเคลม, VIN, ยี่ห้อ/รุ่น, ทะเบียน, VAT 7% | PDF p.7 (SIT invoice) | Planned |
| **ใบส่งสินค้าชั่วคราว** | stock.picking | product code, รายการ, จำนวน, ราคา, ส่วนลด%, ลงนาม 3 ตำแหน่ง | PDF p.7 (Delivery Note) | Planned |
| **ใบรายการอะไหล่** | dismantling.line | part name, ประเภท, จำนวน, ราคา | PDF p.1-2 (ใบรายการอะไหล่) | Planned |
| **ROI Report** | acquired + sale.order | total_cost, actual_revenue, profit, roi%, sold_% | — | Planned |

### 8.2 Product Code Format

จาก Invoice ตัวอย่าง: **ATP-300-TIP** (format: `{part_code}-{spec_code}`)

- DP ใช้ product code ที่มีรหัสเฉพาะ (ยังไม่ชัดเจนว่า auto-generate หรือ manual)
- ต้องถาม user เรื่อง naming convention

---

## 9. Open Questions for User

### 9.1 Assessment Process (ท่อน 1)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q1 | **Batch Import:** รายการซาก 15-20 คัน/สัปดาห์ที่ได้จาก email — มาในรูปแบบไหน? (Excel? PDF? ข้อมูลอะไรบ้าง?) | ต้อง design import wizard ให้ตรงกับ format ที่ได้รับ | สมมติว่ากรอกมือทีละคัน |
| Q2 | **ECF → Insurance Value:** เมื่อกรอก ECF claim number แล้ว ดึงทุนประกันจากที่ไหน? กรอกมือจาก EMCS? หรืออยากให้ auto-fill? | ถ้า auto-fill ต้อง integrate กับ EMCS API | สมมติว่ากรอกมือ |
| Q3 | **ราคา % ซื้อซาก:** 15% (แจ้งจอด) / 25% (ไม่แจ้งจอด) — ค่านี้เปลี่ยนบ่อยแค่ไหน? ต่อรองเป็นรายคันได้หรือไม่? | ถ้าต่อรองรายคัน ต้อง override suggested_price ได้ | สมมติว่าใช้ % เดียวทุกคัน, แต่ override ได้ (target_price) |
| Q4 | **Field Survey:** สายสืบออกไปดูรถหน้างาน — ใช้มือถือกรอก Odoo ได้หรือไม่? หรือต้อง print checklist แล้วกลับมากรอก? | มีผลต่อ UX design (mobile-friendly form vs print PDF) | สมมติว่า print checklist + กลับมากรอก |
| Q5 | **รูปถ่าย:** จำนวนรูปต่อคัน? ขนาดไฟล์? ใครเป็นคนอัพโหลด (สายสืบ หรือ H/O)? | Storage + permission design | สมมติว่า H/O อัพโหลด, ~5-10 รูป/คัน |
| Q6 | **Offering ผ่าน LINE กลุ่ม:** ข้อมูลที่ส่งไป LINE ต้อง format ยังไง? ต้องการปุ่ม "Copy to Clipboard" หรือ auto-post? | LINE integration scope | สมมติว่า manual copy-paste, ยังไม่ทำ LINE integration |
| Q7 | **Offering Deadline:** 30 วันเป็น default หรือเปลี่ยนได้ตามประกัน? | ต้องรู้ว่า deadline มาจากไหน | สมมติว่ากรอกเอง per คัน |
| Q8 | **Overall Condition (สภาพโดยรวม):** 5 ตัวเลือกที่ให้ไว้ (Normal Wear/Accident/Flood/Fire/Other) ครอบคลุมพอหรือไม่? | อาจมีประเภทอื่นที่ไม่ได้ระบุ | สมมติว่าครอบคลุม |
| Q9 | **Expected Price ต่อ part:** ใครเป็นคนกรอก? ราคาตลาดหรือราคาต้นทุน? มี reference ราคาจากที่ไหน? | ถ้าดึงจาก pricelist ต้อง integrate | สมมติว่า H/O กรอกมือจากประสบการณ์ |

### 9.2 Acquired & Procurement (ท่อน 2)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q10 | **Vendor:** ขายยกคัน → vendor = ทิพยฯ เสมอ? หรือมี supplier อื่น? | ถ้ามีหลาย supplier ต้อง support multi-vendor | สมมติว่าเลือก vendor ได้ แต่ส่วนใหญ่เป็นทิพยฯ |
| Q11 | **Purchase Price:** ราคาซื้อจริง = suggested_price เสมอ? หรือต่อรองได้? | ถ้าต่อรอง ราคา PO อาจไม่ตรง suggested_price | สมมติว่าต่อรองได้ (purchase_price กรอกอิสระ) |
| Q12 | **ค่าขนส่ง:** transport_cost — ใครจ่าย? มีอัตราคงที่ (กทม. ฟรี/ต่างจังหวัดตามระยะ)? | อาจ auto-calculate จาก zone | สมมติว่ากรอกมือ |
| Q13 | **PO Approval:** DP-AC-005 มี 4 ลงนาม — ต้องมี approval workflow ใน Odoo หรือแค่ print แล้วเซ็นมือ? | ถ้า digital approval ต้องทำ purchase.order approval + access control | สมมติว่า print + เซ็นมือ ก่อน, digital approval ทีหลัง |
| Q14 | **ใบปล่อยรถ:** เป็นเอกสารจากทิพยฯ หรือ DP ออกเอง? ต้อง upload scan เข้าระบบหรือไม่? | Document management scope | สมมติว่าทิพยฯ ออก, DP แค่ track วันที่ได้รับ |
| Q15 | **VIN (เลขตัวถัง):** ได้มาจากไหน? ตอนไหน? (ตั้งแต่ Assessment หรือ Acquired?) | Assessment มี vehicle_vin แต่ไม่ required, Acquired มี vin ที่ required | สมมติว่ากรอก VIN ที่ Assessment (optional) แล้ว copy ไป Acquired (required) |

### 9.3 Path A: Broker / Sell Whole (ท่อน 3 — ยังไม่ได้ code)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q16 | **มัดจำ 5,000 บาท:** ลูกค้าจ่ายมัดจำ → DP ออกใบเสร็จมัดจำ → ยังไม่ปล่อยรถ → ลูกค้าจ่ายครบ → ทำ SO — กระบวนการมัดจำ ต้อง track ใน Odoo หรือแค่หมายเหตุ? | ถ้า track ต้องทำ advance payment invoice | สมมติว่าใช้ sale.advance.payment.inv |
| Q17 | **ราคาขายยกคัน:** กำหนดยังไง? เท่ากับ suggested_price หรือคนละราคา? | pricing strategy | สมมติว่า offering_sale_price กรอกอิสระ (เจรจากับลูกค้า) |
| Q18 | **Dropship Route:** ทิพยฯ ปล่อยรถตรงให้ลูกค้า — ลูกค้าไปรับเองที่ศูนย์/อู่? หรือ DP ต้องจัดส่ง? | ถ้า DP จัดส่ง ไม่ใช่ dropship แท้ | สมมติว่าลูกค้าไปรับเอง (ได้ใบปล่อย → ไปรับ) |
| Q19 | **SO ขายยกคัน:** ต้องออก Invoice/Tax Invoice ด้วยหรือไม่? credit term กี่วัน? | ถ้าต้องออก invoice ต้อง wire เข้า account.move | สมมติว่าต้อง — DP ขาย DP ต้องออกใบกำกับภาษี |
| Q20 | **ขายได้มากกว่า 1 คนเสนอ:** ถ้ามีลูกค้าหลายคนสนใจ DP เลือกยังไง? ต้อง track ผู้เสนอหลายคน? | ถ้ามี bidding ต้อง design model เพิ่ม | สมมติว่าเลือก 1 คนแล้วกรอก offering_customer_id |

### 9.4 Dismantling & Parts Sales (ท่อน 2-3)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q21 | **Actual vs Assessed:** ตอนรื้อจริง ช่างพบว่า origin/condition ต่างจากที่ประเมิน — เกิดบ่อยแค่ไหน? | ถ้าบ่อย ต้อง UX ง่ายในการเปลี่ยน | สมมติว่าเกิดบ้าง → มี actual_origin/condition per line |
| Q22 | **Parts ที่ไม่อยู่ใน BOM Template:** ตอนรื้อเจอ part ที่ไม่ได้ประเมินไว้ — เพิ่มได้เลยหรือไม่? | ถ้าเพิ่มได้ต้อง create product on-the-fly | สมมติว่าเพิ่มได้ (manual add dismantling.line) |
| Q23 | **ราคาขายอะไหล่:** ใช้ pricelist? มี discount? หรือเจรจารายชิ้น? | pricing model for parts | สมมติว่า standard Odoo pricelist |
| Q24 | **QC Process:** ตรวจสอบอะไหล่ก่อนส่ง — ต้องมี QC step ใน Odoo (quality module) หรือแค่ confirm delivery? | ถ้าต้อง QC ต้อง install quality module | สมมติว่าแค่ confirm delivery (ไม่มี QC module) |
| Q25 | **Multi-customer per vehicle:** 1 คันรื้อ → ขาย parts ให้หลายลูกค้า — DP track ยังไงว่าคันนี้ขายหมดแล้ว? | sold_percentage compute logic | สมมติว่า track จาก sale.order.line → lot → acquired |

### 9.5 Settlement & Finance (ท่อน 2-3)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q26 | **DP-AC-005 (แบบขออนุมัติจ่าย):** เอกสารนี้ทำเป็น batch (หลายคันรวมกัน) ตามตัวอย่าง PDF — batch ตาม period ไหน? (สัปดาห์/เดือน?) | Report grouping | สมมติว่า batch ตามที่ user เลือก (wizard) |
| Q27 | **ส่วนลด %:** DP-AC-005 มีคอลัมน์ส่วนลด% — ส่วนลดนี้คืออะไร? มาจากไหน? | ไม่เห็น logic ส่วนลดใน requirements | สมมติว่ามี field ให้กรอก |
| Q28 | **VAT 7%:** DP ต้องเรียก VAT ทุกครั้ง? หรือบางกรณียกเว้น? | tax configuration | สมมติว่า VAT 7% ทุกรายการ |
| Q29 | **โอนกรรมสิทธิ์:** ทุกคันต้องโอนหรือไม่? (ถ้าขายยกคัน ลูกค้าอาจโอนเองกับกรมขนส่ง?) | ownership_transfer_status scope | สมมติว่า track ได้ แต่ไม่บังคับ (มี N/A option) |
| Q30 | **Payment to Insurance:** จ่ายค่าซากให้ทิพยฯ — จ่ายผ่าน Odoo (account.payment) หรือแค่ track วันที่+จำนวน? | ถ้าผ่าน Odoo ต้อง wire เข้า account module | สมมติว่า track วันที่+จำนวน (ไม่ทำ payment reconciliation) |
| Q31 | **Credit Term:** DP มี credit term กับทิพยฯ กี่วัน? (ตัวอย่าง invoice แสดง 30 วัน) | payment term configuration | สมมติว่า 30 วัน |
| Q32 | **วางบิลทุกวันจันทร์:** PDF ระบุว่ารวมส่งทิพยฯ ทุกจันทร์ — ต้อง automate batch billing หรือ manual? | ถ้า automate ต้อง scheduled action | สมมติว่า manual (user เลือก invoice แล้วส่ง batch) |

### 9.6 Product & Inventory

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q33 | **Product Code (e.g. ATP-300-TIP):** format นี้มาจากไหน? auto-generate หรือกรอกเอง? มี pattern คงที่ไหม? | internal_reference format | สมมติว่ากรอกเอง (ยังไม่ auto-generate) |
| Q34 | **Product Description ใน Invoice:** ต้องแสดงข้อมูลอะไรบ้าง? (เลขเคลม, VIN, ยี่ห้อ/รุ่น, ทะเบียน — ตาม invoice ตัวอย่าง) | invoice line description template | สมมติว่า customize invoice line description |
| Q35 | **Stock Location:** อะไหล่เก็บที่เดียว (โกดัง DP) หรือหลายที่? | warehouse/location configuration | สมมติว่า 1 warehouse, per-category location (ถ้ามี) |
| Q36 | **ร้านอะไหล่ (Supplier):** DP มีร้านอะไหล่เป็น vendor ด้วย? (สั่งอะไหล่จากร้าน) หรือ DP ขายอย่างเดียว? | PDF p.1-2 แสดง flow สั่งอะไหล่จากร้าน | ยังไม่ชัดเจนว่า scope นี้อยู่ใน module เดียวกันหรือไม่ |

### 9.7 User & Permission

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q37 | **User Role:** มีกี่ role? (สายสืบ, H/O staff, ผู้จัดการ, บัญชี, ช่าง) → แต่ละ role เห็น/ทำอะไรได้บ้าง? | access control (ir.model.access + record rules) | สมมติว่า 2 groups: user (read/create) + manager (full) |
| Q38 | **Multi-company:** DP มีบริษัทเดียว หรือหลายบริษัท? | company_id scope | สมมติว่า single company |
| Q39 | **จำนวน User:** คนใช้งานกี่คน? ใช้พร้อมกันกี่คน? | server sizing + license | ยังไม่ทราบ |

### 9.8 External Integration (อนาคต)

| # | คำถาม | เหตุผลที่ต้องถาม | Assumption ปัจจุบัน |
|---|---|---|---|
| Q40 | **ePart/EMCS/E-Billing API:** ระบบ BlueVenture มี API ให้เชื่อมหรือไม่? มี documentation? | integration feasibility | สมมติว่าไม่มี API (manual copy-paste ไปก่อน) |
| Q41 | **LINE Notify/API:** ต้องการ auto-post ไป LINE กลุ่ม หรือ copy-paste พอ? | LINE integration scope | สมมติว่า copy-paste (Phase 2 อาจทำ LINE Notify) |
| Q42 | **eCommerce:** ต้องการขายอะไหล่ online (Odoo eCommerce) ในอนาคตหรือไม่? | product variant design ต้องรองรับ | สมมติว่าอนาคต (variant design รองรับแล้ว) |

---

## 10. Risk & Assumptions

### 10.1 Assumptions ที่สำคัญ

| # | Assumption | Impact ถ้าผิด |
|---|---|---|
| A1 | DP มี supplier หลักเจ้าเดียว (ทิพยประกันภัย) | ถ้ามีหลายเจ้า ต้อง support multi-insurance workflow |
| A2 | ราคาซื้อซากใช้สูตร % เดียวกันทุกคัน | ถ้าต่อรองรายคัน ต้องมี override mechanism (มีแล้ว: target_price) |
| A3 | สายสืบไม่ได้ใช้ Odoo mobile | ถ้าใช้ ต้อง optimize form สำหรับ mobile |
| A4 | DP ไม่ต้องการ real-time integration กับ ePart/EMCS | ถ้าต้องการ scope เพิ่มมาก (API development) |
| A5 | 1 คัน = 1 assessment (ไม่มี re-assessment) | ถ้า re-assess ต้อง reset flow |
| A6 | Dropship ขายยกคัน = ลูกค้าไปรับเองที่ศูนย์/อู่ | ถ้า DP จัดส่ง ต้องใช้ delivery order ไม่ใช่ dropship |
| A7 | Payment to insurance ไม่ผ่าน Odoo accounting | ถ้าผ่าน ต้อง wire เข้า AP + bank reconciliation |
| A8 | QC ไม่ต้องทำใน Odoo | ถ้าต้อง ต้อง install quality module + QC workflow |

### 10.2 Risks

| # | Risk | Probability | Impact | Mitigation |
|---|---|---|---|---|
| R1 | User ไม่คุ้นเคยกับ Odoo → adoption ช้า | สูง | สูง | Training + ทำ checklist print ให้เหมือนของเดิม |
| R2 | ePart/EMCS workflow เปลี่ยน | ต่ำ | กลาง | Design loosely coupled (manual entry fallback) |
| R3 | Volume เพิ่ม (>20 คัน/สัปดาห์) | กลาง | ต่ำ | Batch import wizard scales |
| R4 | Product variant explosion (มาก spec × parts × origin × condition) | กลาง | กลาง | Dynamic variant (create-on-demand, ไม่ pre-create) |
| R5 | Unbuild bypass อาจมีปัญหากับ Odoo upgrade | ต่ำ | สูง | Document workaround, re-test on upgrade |
| R6 | DP-AC-005 approval เปลี่ยนผู้ลงนาม | ต่ำ | ต่ำ | Configurable signers |

---

## 11. Implementation Phases

### Phase 1: Core Lifecycle (ท่อน 1+2) — **DONE**

| Deliverable | Status |
|---|---|
| Assessment model + states (6 states, 5 paths) | ✅ Done |
| Assessment lines from BOM Template | ✅ Done |
| Assessment images with category | ✅ Done |
| Insurance fields (ECF, ทุนประกัน, แจ้งจอด, suggested_price) | ✅ Done |
| Offering wait state with deadline | ✅ Done |
| Acquired model + states (9 states, 2 paths) | ✅ Done |
| PO auto-creation + analytic account | ✅ Done |
| VIN lot tracking + stock confirm | ✅ Done |
| Dismantling order + unbuild + stock moves | ✅ Done |
| Release & Settlement tracking | ✅ Done |

### Phase 2: Path A + Parts Sales (ท่อน 3) — **PLANNED**

| Deliverable | Priority |
|---|---|
| SO creation for sell_whole (Dropship route) | High |
| Deposit tracking (มัดจำ 5,000) | High |
| Actual revenue compute from SO lines | High |
| sold_percentage compute | Medium |

### Phase 3: Reports & Documents (ท่อน 4) — **PLANNED**

| Deliverable | Priority |
|---|---|
| ใบประเมินซากรถ (Checklist PDF) | High |
| แบบขออนุมัติจ่าย (DP-AC-005) | High |
| Invoice/Tax Invoice customization | High |
| Delivery Note customization | Medium |
| Batch Intake wizard (CSV/Excel import) | Medium |

### Phase 4: Enhancement — **FUTURE**

| Deliverable | Priority |
|---|---|
| Digital PO approval workflow | Medium |
| LINE Notify integration | Low |
| ePart/EMCS API integration | Low |
| eCommerce (online parts catalog) | Low |
| Dashboard & Analytics | Medium |
| Mobile-optimized assessment form | Medium |

---

## Appendix A: Data Model Summary

```
itx.revival.assessment (ท่อน 1)
├── itx.revival.assessment.line (per-part assessment)
├── itx.revival.assessment.image (field survey photos)
└── → creates → itx.revival.acquired

itx.revival.acquired (ท่อน 2)
├── → creates → purchase.order (PO ซื้อซาก)
├── → creates → sale.order (SO ขายยกคัน — Path A, planned)
├── → creates → account.analytic.account (cost center)
├── → creates → itx.revival.dismantling (Path B)
│     ├── itx.revival.dismantling.line (per-part actual)
│     └── → creates → mrp.unbuild + stock.move (consume + produce)
└── stock.lot (VIN tracking per product)
```

## Appendix B: State Machine Diagram

```
                    ASSESSMENT                              ACQUIRED
                    ─────────                              ─────────
                                                          
  ┌───────┐                                   ┌───────┐
  │ draft │                                   │ draft │
  └───┬───┘                                   └───┬───┘
      │ action_assess                              │ action_create_po
  ┌───┴────┐                                  ┌────┴─────┐
  │assessed│                                  │po_created│
  └┬──┬──┬─┘                                  └────┬─────┘
   │  │  │                                         │ action_request_release
   │  │  │ action_offer                       ┌────┴─────┐
   │  │  └──┐                                 │releasing │
   │  │  ┌──┴────┐                            └──┬────┬──┘
   │  │  │offering│                              │    │
   │  │  └┬──┬──┬┘                               │    │ action_delivered (Path A)
   │  │   │  │  │ action_sold              ┌─────┴┐  ┌┴────────┐
   │  │   │  │  └──┐                       │stocked│  │delivered│
   │  │   │  │  ┌──┴──┐                    └──┬───┘  └────┬────┘
   │  │   │  │  │ sold│──→ Create Acquired    │           │
   │  │   │  │  └─────┘                       │           │
   │  │   │  │                           ┌────┴──────┐    │
   │  │   │  └─┐ action_offering_dismantle│dismantling│    │
   │  │   │    └─┐                        └────┬─────┘    │
   │  │   │      │                        ┌────┴──────┐   │
   │  └───┼──────┼── action_decide_dismantle           │   │
   │      │      │                        │parts_ready│   │
   │   ┌──┴──┐ ┌─┴────────┐              └────┬──────┘   │
   │   │disma│ │returned   │                   │          │
   │   │ntle │ │(END)      │              ┌────┴──────┐   │
   │   └──┬──┘ └──────────┘              │ settling  │←──┘
   │      │                              └────┬──────┘
   │      └──→ Create Acquired           ┌────┴──────┐
   │                                     │  closed   │
   └── action_return                     │  (END)    │
       └→ returned (END)                 └───────────┘
```

---

*Document generated: 2026-04-14*  
*Module version: 19.0.2.0.0*  
*Prepared by: IT Expert Training & Outsourcing Co.*
