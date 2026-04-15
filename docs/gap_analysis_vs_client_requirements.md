# Gap Analysis: ระบบปัจจุบัน vs ความต้องการลูกค้า (PDF ver2)

**Date:** 2026-04-12
**Source:** เอกสารการทำงานส่งให้ทีม odoo ver2.pdf (หน้า 7-11)
**Client:** DP Survey & Law Co., Ltd. (ทิพยประกันภัย เป็น supplier หลัก)

---

## 1. Flow ที่ลูกค้าทำจริง (สรุปจาก PDF)

### ขั้นตอนร่วม (ทั้ง 2 เส้นทาง)
1. รับรายการซากจากทิพยประกันภัยทาง email (~15-20 คัน/สัปดาห์)
2. ตรวจสอบเลขเคลม ECF → ดูสภาพรถ + รูปจากระบบศูนย์
3. ประเมินความเสียหาย + ตัดสินใจ: ขายยกคัน / แยกอะไหล่ / ไม่ซื้อ
   - **PDF เน้น:** ต้องถ่ายรูปหน้างาน + อัพโหลดรูปเข้า Odoo
4. เสนอราคาซื้อซาก = % ของทุนประกัน
   - แจ้งจอด → 15%
   - ไม่แจ้งจอด → 25%

### เส้นทาง A: ขายยกคัน
5. ประกาศขายผ่าน LINE กลุ่ม (ยี่ห้อ ปี ทะเบียน สถานที่จอด)
6. รับชำระจากลูกค้า (มัดจำ 5,000 → ชำระครบ → ใบสั่งขาย)
7. ขอใบปล่อยรถจากทิพยฯ
8. แจ้งผลทิพยฯ — **เงื่อนไข: DP ซื้อได้ก็ต่อเมื่อมีคนซื้อ+จ่ายครบแล้วเท่านั้น**
9. โอนเงินค่าซากให้ทิพยฯ → รับเล่มทะเบียน → โอนกรรมสิทธิ์

### เส้นทาง B: แยกอะไหล่
5. ขอใบปล่อยรถ → ยกรถไปเก็บที่โกดัง
6. ทีมช่างรื้อ → ลงข้อมูลอะไหล่เข้าสต็อก
7. ลูกค้ามาซื้อ part จากสต็อก
8. ลูกค้าชำระเงิน → SO + ใบเสร็จ + ใบกำกับภาษี
9. QC part → ออกใบจัดส่ง
10. จัดส่ง → ลูกค้าเซ็นรับ = ปิดงาน

**หมายเหตุ:** การชำระค่าซากกับทิพยฯ สามารถทำก่อนหรือหลังปิดงานขายได้

---

## 2. GAP รายข้อ

### 2.1 Critical Gaps (กระทบ flow หลัก)

| # | ความต้องการ (PDF) | ระบบปัจจุบัน | Gap |
|---|---|---|---|
| G1 | **Flow ยกคัน = broker model** (DP หาคนซื้อก่อน → คนซื้อจ่ายครบ → แล้วค่อยซื้อจากประกัน) | Acquired สมมติว่า DP ซื้อก่อน stock เก็บ รอขาย | ลำดับกลับกัน: จริง=ขายก่อนซื้อ, ระบบ=ซื้อก่อนขาย (เฉพาะ sell_whole) |
| G2 | **ทุนประกัน + แจ้งจอด/ไม่แจ้งจอด** → สูตรคำนวณราคาเสนอซื้อ (15% / 25%) | มีแค่ asking_price + target_price กรอกมือ | ไม่มี insurance_value, is_reported, auto-calculate |
| G3 | **เลขเคลม ECF** เป็น key identifier | ไม่มี field | ไม่มี ecf_claim_number |
| G4 | **รูปถ่ายตอน Assessment** (PDF ขีดเส้นใต้แดงเน้น) | image_ids อยู่บน Acquired เท่านั้น | Assessment ไม่มี image upload |
| G5 | **ทะเบียนรถ (plate number)** ใช้เป็น identifier สำคัญใน PDF | ไม่มี field | ไม่มี plate_number |
| G6 | **มัดจำ 5,000 + partial payment** (ออกใบเสร็จมัดจำ ยังไม่ปล่อยรถ) | ไม่มี deposit tracking | ต้อง integrate sale.advance.payment.inv |
| G7 | **ใบปล่อยรถ + โอนกรรมสิทธิ์** tracking | ไม่มี — state จบที่ completed | ไม่มี release_doc_date, ownership_transfer_status |
| G8 | **ใบขออนุมัติจ่าย** (DP-AC-005) เอกสารภายใน DP | ไม่มี — ใช้แค่ PO | อาจ map เป็น PO approval + custom report |

### 2.2 Secondary Gaps (phase 2 ได้)

| # | ความต้องการ | Gap |
|---|---|---|
| G9 | Batch intake (15-20 คัน/สัปดาห์ จาก email) | ไม่มี batch/group model |
| G10 | ช่องทางขาย LINE กลุ่ม | integration อนาคต |
| G11 | เอกสารประกอบ: ใบสั่งขาย, ใบเสร็จ, ใบกำกับภาษี, ใบจัดส่ง | Odoo standard sale→invoice→delivery มีอยู่แล้ว แต่ยังไม่ wire เข้ากับ revival |

### 2.3 ตรงกันแล้ว

| ความต้องการ | Module/Feature |
|---|---|
| ประเมินซากรถ + checklist | Assessment + assessment.line |
| ตัดสินใจ ซื้อ/ไม่ซื้อ/ยกคัน/แยก | decision field |
| สร้าง PO ซื้อซาก | action_create_po |
| แยกชิ้นส่วน + ลงสต็อก | Dismantling + unbuild + stock.move |
| VIN tracking + lot/serial | stock.lot with itx_vin (กำลังทำ) |
| Analytic per คัน | 1 acquired = 1 analytic account |
| ROI tracking | expected/actual revenue + profit + roi |
| ราคาคาดการณ์ต่อ part | assessment.line.expected_price |
| ช่างรื้อ | dismantling.technician_id |

---

## 3. เอกสารตัวอย่างจาก PDF

1. **ใบแจ้งหนี้/ใบกำกับภาษี** (Invoice/Tax Invoice) — DP ออกให้ลูกค้าเมื่อขาย part
   - มี: product code (ATP-300-TIP), รายละเอียด part, เลขเคลม, เลขตัวถัง, ยี่ห้อ/รุ่น, ทะเบียน
2. **ใบประเมินซากรถ** (Checklist) — ฟอร์มกระดาษ 20 ช่อง สายสืบกรอกหน้างาน
   - มี: ยี่ห้อ รุ่น ปี ทะเบียน สถานที่จอด สีรถ เลขไมล์
   - columns: สภาพดี / สภาพพอใช้
   - checkbox: มาซื้อ / ไม่มาซื้อ
3. **แบบขออนุมัติจ่าย** (DP-AC-005) — เอกสารภายใน approve การจ่ายเงินซื้อซากให้ทิพยฯ
   - รายการรถ + ราคา + ส่วนลด% + VAT 7% + ลงนาม 4 ตำแหน่ง

---

## 4. จุดที่ต้องระวังเป็นพิเศษ

### Flow ยกคันเป็น Broker Model
DP **ไม่ซื้อซากจนกว่าจะมีลูกค้าจ่ายครบ** ดังนั้น flow ยกคัน:
- Assessment → find buyer → buyer pays → PO to insurance → release car → transfer to buyer
- **ไม่ใช่:** Assessment → PO → stock in → find buyer → sell

สำหรับ flow **แยกอะไหล่** DP ซื้อจริง ยกมาเก็บ รื้อ ขาย — ตรงกับระบบปัจจุบัน

### ทิพยประกันภัยเป็น Supplier เดียว (ปัจจุบัน)
ระบบควรรองรับ supplier หลายเจ้าในอนาคต แต่ปัจจุบัน flow ผูกกับระบบ ECF ของทิพยฯ
