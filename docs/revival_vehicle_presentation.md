# ITX Revival Vehicle — สรุประบบเพื่อนำเสนอ User

**วันที่:** 2026-04-06
**สถานะ:** กำลัง Implement — พร้อม Review

---

## ภาพรวมระบบ

ระบบจัดการวงจรชีวิตซากรถ ตั้งแต่ประเมิน → ซื้อ → แตกชิ้นส่วน → ขาย → ติดตาม ROI

```
สายสืบเจอซากรถ
      │
      ▼
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  DOC 1       │     │  DOC 2       │     │  DOC 3       │
│  Assessment  │ ──▶ │  Acquired    │ ──▶ │  Dismantling │
│  ประเมิน     │     │  ซื้อเข้ามา   │     │  แตกชิ้นส่วน  │
└──────────────┘     └──────────────┘     └──────────────┘
                                                │
                                                ▼
                                          อะไหล่เข้า Stock
                                          พร้อมขาย
```

---

## DOC 1: Assessment (แบบประเมินซากรถ)

### ใครทำอะไร

| ขั้นตอน | ใครทำ | ทำอะไร |
|---|---|---|
| 1. สร้างเอกสาร | สายสืบ / H/O | กรอกข้อมูลรถ: ยี่ห้อ รุ่น สเปค ที่อยู่ ราคาที่เจ้าของตั้ง |
| 2. เตรียมข้อมูล | H/O | กด Generate Lines → ระบบสร้างรายการอะไหล่อัตโนมัติ |
| 3. แก้ไข BOM | H/O | เพิ่ม/ลบ/แก้ชิ้นส่วนใน BOM (ถ้าต้องการ) แล้ว Sync กลับ |
| 4. ตั้งราคา | H/O | กรอก Target Price + Expected Price ต่อชิ้น → เห็น ROI ทันที |
| 5. สำรวจหน้างาน | สายสืบ | ไปดูรถจริง กรอกผ่าน Odoo: เจอ/ไม่เจอ จำนวน สภาพ หมายเหตุ |
| 6. ตัดสินใจ | H/O | ไม่ซื้อ / ซื้อขายทั้งคัน / ซื้อแตก Part |

### สถานะเอกสาร

```
Draft ──▶ Preparing ──▶ Complete ──▶ Acquired (สร้าง DOC 2)
                                  ──▶ Cancelled (ไม่ซื้อ)
```

### ตัวอย่างหน้าจอ

**Header:**
```
เลขที่: ASM/2026/0001
สเปครถ: Honda Civic FD 1.8 S i-VTEC          Body Type: Sedan
ที่อยู่ซาก: ลำลูกกา คลอง 4
ราคาเจ้าของตั้ง: 110,000    ราคาเสนอซื้อ: 90,000
รายได้คาดการณ์: 102,000     กำไร: 12,000     ROI: 13%
```

**รายการอะไหล่ (ตัวอย่างบางชิ้น):**

| ชิ้นส่วน | Origin | Condition | จำนวน | ราคาคาด | เจอ | จำนวนจริง | สภาพจริง | หมายเหตุ |
|---|---|---|---|---|---|---|---|---|
| กันชนหน้า | OEM | Fair | 1 | 2,500 | ✓ | 1 | Fair | แตกมุมซ้าย |
| ไฟหน้าซ้าย | OEM | Fair | 1 | 3,000 | ✓ | 1 | Good | ใสไม่มีรอย |
| ไฟหน้าขวา | OEM | Fair | 1 | 3,000 | ✗ | 0 | — | หายไป |
| ยาง | OEM | Fair | 4 | 8,000 | ✓ | 3 | Good | Bridgestone 2025 ดอก 90% |
| เครื่องยนต์ | OEM | Fair | 1 | 25,000 | ✓ | 1 | Poor | เครื่องแตก |

---

## ระบบ Master Data (ข้อมูลใช้ซ้ำได้)

### 3 ชั้นของข้อมูล

```
ชั้น 1: Template BOM (ระดับ Body Type)
        "รถ Sedan มีชิ้นส่วน ~54 ชิ้น"
        → ข้อมูลกลาง ใช้กับทุกยี่ห้อ/รุ่น ของ Sedan
        → ตั้งค่าครั้งเดียว

ชั้น 2: mrp.bom + Product (ระดับ Spec)
        "Honda Civic FD 1.8S มี BOM ชิ้นส่วน 54 ชิ้น + ราคา"
        → สร้างอัตโนมัติครั้งแรกที่ประเมินรถ spec นี้
        → แก้ไขได้ (เพิ่ม/ลบ/แก้ราคา)
        → ซื้อรถ spec เดียวกันอีกคัน ใช้ BOM เดิมได้เลย

ชั้น 3: Assessment Line (ระดับ Transaction)
        "รถคันนี้ VIN: ABC123 สายสืบเจอ 48 ชิ้นจาก 54"
        → เฉพาะคัน ใช้ครั้งเดียว
```

### ประโยชน์

- **ครั้งแรก:** สร้าง Product + BOM อัตโนมัติจาก Template (~54 ชิ้นส่วน)
- **ครั้งถัดไป:** Spec เดียวกัน → ใช้ BOM เดิม ไม่ต้องสร้างใหม่ ราคา up-to-date
- **Product ไม่ซ้ำ:** ใช้ UK (Spec + ชื่ออะไหล่ + Origin + Condition)

---

## DOC 2: Acquired (รถที่ซื้อแล้ว)

### สถานะ

```
Draft ──▶ Purchased (สร้าง PO) ──▶ Stocked (รับเข้า Stock) ──▶ Completed
```

### ข้อมูลสำคัญ

| หมวด | ข้อมูล |
|---|---|
| แหล่งที่มา | เลข Assessment, สเปครถ, VIN |
| การซื้อ | Vendor, PO, ราคาซื้อจริง, วันที่ |
| ต้นทุน | ราคาซื้อ + ค่าขนส่ง + ค่ารื้อ + อื่นๆ = ต้นทุนรวม |
| ROI | รายได้จริง, กำไร, % ขายแล้ว |
| Analytic | 1 คัน = 1 Analytic Account (ดู P&L ต่อคันได้) |

### PO สร้างอัตโนมัติ

- กรอก Vendor + ราคา → กด Create PO
- ระบบสร้าง Purchase Order ให้ พร้อมผูก Analytic Account
- Confirm PO → รับของ → Stock In อัตโนมัติ

---

## DOC 3: Dismantling (แตกชิ้นส่วน) — กำลังพัฒนา

### Flow ที่วางไว้

```
สร้างเอกสาร Dismantling จาก Acquired
      │
      ▼
Copy assessment lines มา
+ สายสืบ/ช่าง กรอกข้อมูลจริง:
  - Origin จริง (OEM/Aftermarket/Reconditioned)
  - Condition จริง (New/Good/Fair/Poor)
  - ราคาขายจริง
      │
      ▼
สร้าง Product ใหม่ตาม actual origin + condition
(เฉพาะที่รื้อออกมาจริง → ไม่มี product ขยะ)
      │
      ▼
Unbuild Order (Odoo MRP)
  - Stock OUT ซากรถ  ×1
  - Stock IN อะไหล่   ×N  (อัตโนมัติ)
      │
      ▼
อะไหล่พร้อมขาย
```

---

## ตัวอย่าง Flow จริง ครบ Loop

```
1. สายสืบโทรมา: "เจอ Civic FD ที่ลำลูกกา เจ้าของขอ 110,000"

2. H/O สร้าง Assessment
   → เลือก Spec: Honda Civic FD 1.8S
   → กด Generate Lines → ได้ 54 ชิ้นส่วน + BOM อัตโนมัติ
   → ตั้ง Target Price: 90,000
   → กรอก Expected Price ต่อชิ้น → ROI = 13%

3. สายสืบไปสำรวจ
   → กรอกผ่าน Odoo: เจอ 48 ชิ้น ไม่เจอ 6 ชิ้น
   → ยาง 4 เส้น เจอ 3 เส้นที่ใช้ได้
   → ภาพรวม: ชนหน้า เครื่องแตก ตัวถังดี 70%

4. H/O ตัดสินใจ: ซื้อแตก Part
   → กด Create Acquired

5. Acquired: กรอก Vendor + ราคาซื้อ 85,000
   → กด Create PO → Odoo สร้าง PO ให้
   → Confirm PO → รับของ → ซากรถเข้า Stock

6. Dismantling: (กำลังพัฒนา)
   → ช่างรื้อ → กรอกข้อมูลจริง
   → Unbuild → อะไหล่ 48 ชิ้นเข้า Stock
   → พร้อมขาย

7. ขายอะไหล่ผ่าน Odoo Sale Order
   → ผูก Analytic Account ต่อคัน
   → ดู P&L, ROI จริง ต่อซากรถแต่ละคัน
```

---

## สิ่งที่พัฒนาเสร็จแล้ว

| รายการ | สถานะ |
|---|---|
| DOC 1: Assessment — full flow | ✅ ใช้งานได้ |
| Generate Lines จาก Template BOM | ✅ |
| Spec-level BOM (master, reusable) | ✅ |
| Auto create Product (UK ไม่ซ้ำ) | ✅ |
| Edit BOM / Sync from BOM | ✅ |
| ROI calculation | ✅ |
| Field Survey (is_found, qty, condition) | ✅ |
| DOC 2: Acquired — basic flow | ✅ |
| Auto create PO | ✅ |
| Analytic Account per vehicle | ✅ |
| DOC 3: Dismantling | 🔲 กำลังพัฒนา |
| Unbuild integration | 🔲 กำลังพัฒนา |
| PDF Checklist | 🔲 กำลังพัฒนา |
| ROI Report (dashboard) | 🔲 กำลังพัฒนา |
| Approval Workflow | 🔲 รอ confirm |

---

## คำถามสำหรับ User

1. **Approval:** ต้องการระบบ approve กี่ขั้น? ใครเป็นผู้ approve?
2. **Cost Weight:** ต้นทุนแต่ละชิ้น ใช้ค่าจาก Template BOM ตามนี้ หรือต้องการ weight จาก market price?
3. **Field Survey:** สายสืบ login Odoo กรอกเอง หรือ H/O กรอกให้?
4. **PDF Checklist:** ต้องการข้อมูลอะไรใน checklist นอกจากที่ออกแบบไว้?
5. **Dismantling:** flow ที่ออกแบบไว้ ตรงกับการทำงานจริงหรือไม่?
