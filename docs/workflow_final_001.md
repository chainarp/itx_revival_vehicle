# Workflow Final 001: Salvage Vehicle Lifecycle
# DP Survey & Law Co., Ltd. (Dhipaya Insurance)

**Date:** 2026-04-17
**Status:** Approved (discussed & agreed)
**Source:** PDF ver2 (p.7-11) + gap analysis + discussion

---

## Actors

| Actor | Role |
|---|---|
| Insurance (ทิพยประกันภัย) | Supplier ซากรถ, ส่ง list ทาง email |
| DP H/O | Head Office DP Survey & Law, ตัดสินใจ+จัดการ |
| Field Assessor (สายสืบ) | ไปดูรถหน้างาน ถ่ายรูป |
| Mechanic Team (ทีมช่าง) | รื้อซาก ลงอะไหล่เข้า stock |
| Customer (ลูกค้า) | ซื้อยกคัน หรือ ซื้อ parts |

---

## States

| State | Description |
|---|---|
| `draft` | รับข้อมูลซากมา ยังไม่ประเมิน |
| `assessed` | ประเมินแล้ว รอตัดสินใจ |
| `offering` | ลงขายยกคัน รอลูกค้า (wait state, มี deadline ~30 วัน) |
| `returned` | คืนรถให้ประกัน (ไม่ซื้อ / หมดเวลา) — END |
| `sold` | มีคนซื้อยกคัน + จ่ายครบแล้ว |
| `dismantle` | ตัดสินใจซื้อแยกอะไหล่ |
| `releasing` | ขอใบปล่อยรถจากประกัน |
| `stocked` | รถเข้าโกดัง DP แล้ว (เฉพาะ Path B) |
| `dismantling` | ทีมช่างกำลังรื้อ |
| `parts_ready` | อะไหล่เข้า stock พร้อมขาย |
| `delivered` | ส่งมอบรถให้ลูกค้าแล้ว (เฉพาะ Path A) |
| `settling` | โอนค่าซาก + รอเล่มทะเบียน |
| `closed` | ปิดงาน |

---

## All Possible Paths (per vehicle)

### Path 1: ไม่สนใจ (รถเละมาก)
```
draft → assessed → returned → END
```

### Path 2: ซื้อแยกอะไหล่ (ตัดสินใจทันที)
```
draft → assessed → dismantle → releasing → stocked → dismantling → parts_ready → closed → END
```

### Path 3: เสนอขายยกคัน → ขายได้ (Dropship — ไม่เข้า stock DP)
```
draft → assessed → offering → sold → releasing → delivered → settling → closed → END
```

### Path 4: เสนอขายยกคัน → ขายไม่ได้ → คืน
```
draft → assessed → offering → returned → END
```

### Path 5: เสนอขายยกคัน → เปลี่ยนใจซื้อแยก
```
draft → assessed → offering → dismantle → releasing → stocked → dismantling → parts_ready → closed → END
```

---

## State Transitions

| From | To | Trigger |
|---|---|---|
| `draft` | `assessed` | ประเมินเสร็จ (ดูรูป + field survey) |
| `assessed` | `returned` | ตัดสินใจไม่ซื้อ |
| `assessed` | `dismantle` | ตัดสินใจซื้อแยกอะไหล่ |
| `assessed` | `offering` | ตัดสินใจลงขายยกคัน |
| `offering` | `returned` | หมดเวลา / ยกเลิก |
| `offering` | `dismantle` | เปลี่ยนใจ ซื้อแยกเอง |
| `offering` | `sold` | ลูกค้าจ่ายครบ |
| `sold` | `releasing` | สร้าง SO (dropship) → auto PO → ขอใบปล่อยรถ |
| `dismantle` | `releasing` | สร้าง PO → ขอใบปล่อยรถ |
| `releasing` | `delivered` | (Path A) ลูกค้ารับรถแล้ว |
| `releasing` | `stocked` | (Path B) รถเข้าโกดัง DP |
| `stocked` | `dismantling` | ทีมช่างเริ่มรื้อ |
| `dismantling` | `parts_ready` | รื้อเสร็จ อะไหล่เข้า stock |
| `delivered` | `settling` | เริ่มจ่ายค่าซากให้ประกัน |
| `parts_ready` | `closed` | โอนค่าซาก + รับเล่ม (ทำเมื่อไหร่ก็ได้) |
| `settling` | `closed` | โอนค่าซาก + รับเล่ม + โอนกรรมสิทธิ์ |

---

## Key Design Decisions

### 1. Broker Model (Path A: ยกคัน)
- DP ไม่ซื้อจนกว่าลูกค้าจ่ายครบ (ขายก่อนซื้อ)
- ใช้ Odoo **Dropship Route**: SO → auto PO → ประกันปล่อยรถตรงให้ลูกค้า
- รถไม่เข้า WH/Stock ของ DP

### 2. Inventory Model (Path B: แยกอะไหล่)
- DP ซื้อจริง ยกรถเข้าโกดัง
- PO → Receipt → Unbuild → Parts เข้า stock → ขาย parts ผ่าน SO ปกติ
- การชำระค่าซากให้ประกัน **ไม่ block** การขาย parts

### 3. Offering = Wait State
- มี `offering_deadline` (deadline จากประกัน เช่น 30 วัน)
- สามารถเปลี่ยนไป `returned` หรือ `dismantle` ได้
- เปลี่ยนไป `sold` เมื่อลูกค้าจ่ายครบเท่านั้น

### 4. Pricing Formula (Configurable)
- แจ้งจอด → 15% ของทุนประกัน
- ไม่แจ้งจอด → 25% ของทุนประกัน
- ค่า % อ่านจาก `ir.config_parameter` (แก้ได้ใน Settings)

---

## Fields Added to Assessment (Implemented)

| Group | Field | Type |
|---|---|---|
| Insurance Source | `insurance_partner_id` | Many2one (res.partner) |
| | `ecf_claim_number` | Char, indexed |
| | `claim_date` | Date |
| | `insurance_value` | Monetary |
| | `is_parking_reported` | Boolean |
| | `registration_book_status` | Selection |
| | `suggested_price` | Monetary (computed) |
| Vehicle ID | `plate_number` | Char, indexed |
| | `plate_province` | Char |
| Images | `image_main` | Image (avatar) |
| | `image_ids` | One2many → assessment.image |

### Assessment Image Model (New)
- `image` (Image), `caption` (Char), `category` (Selection: exterior/interior/engine/damage/document/other), `sequence`

---

## Deferred Items (discuss when implementing each section)

| Item | Notes |
|---|---|
| G6: มัดจำ 5,000 + partial payment | `sale.advance.payment.inv` — detail when coding Path A |
| G9: Batch intake 15-20 คัน | Import wizard or CSV — detail when coding intake |
| G10: LINE กลุ่ม integration | Future phase |
| G11: เอกสารพิมพ์ (Invoice, Delivery, Checklist) | Customize QWeb reports — detail when coding reports |
| DP-AC-005 ใบขออนุมัติจ่าย | PO approval + QWeb report — detail when coding payment |
| Product code format (ATP-300-TIP) | Internal reference pattern — detail when coding invoice |
