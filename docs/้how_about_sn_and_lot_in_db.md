เรียบร้อยครับ อ่าน source code Odoo จริงมาแล้ว อธิบายให้:

  โครงสร้าง Database ของ Lot/SN

  ตาราง stock_lot — ตารางหลัก

  stock_lot (Lot/Serial Number)
  ├── name          — เลข Lot/SN (เช่น VIN)
  ├── product_id    → product_product (FK, required)
  ├── company_id    → res_company
  ├── ref           — Internal Reference (optional)
  ├── note          — Description
  ├── location_id   — ถ้า quant อยู่ location เดียว
  └── lot_properties — custom properties

  Unique Constraint (บรรทัด 102-125 ใน source)

  Unique = (product_id + company_id + name)

  หมายความว่า:
    lot "JTDBR9GX10" + กันชนหน้า Civic  → ✓ ได้
    lot "JTDBR9GX10" + ไฟหน้า Civic      → ✓ ได้ (product ต่างกัน)
    lot "JTDBR9GX10" + กันชนหน้า Civic  → ✗ ซ้ำ!

  ความสัมพันธ์กับ Product

  product_template          product_product           stock_lot
  ┌─────────────────┐      ┌──────────────────┐      ┌──────────────────┐
  │ id              │──┐   │ id               │──┐   │ id               │
  │ name            │  │   │ product_tmpl_id  │  │   │ name (VIN)       │
  │ tracking        │  │   │ (variant attrs)  │  │   │ product_id ──────┤→
  product_product
  │  = 'lot'/'serial'│ └──→│                  │  └──→│ company_id       │
  │ is_storable     │      │                  │      │                  │
  │  = True         │      └──────────────────┘      └────────┬─────────┘
  └─────────────────┘                                         │
                                                              │ lot_id
                                                              ▼
                                                     ┌──────────────────┐
                                                     │ stock_quant      │
                                                     │ product_id       │
                                                     │ lot_id ──────────┤→
  stock_lot
                                                     │ location_id      │
                                                     │ quantity         │
                                                     └──────────────────┘

  เงื่อนไขการใช้ Lot ใน Odoo 19

  # stock.lot สร้างได้เฉพาะ product ที่:
  domain = [
      ('tracking', '!=', 'none'),   # ต้องเปิด tracking
      ('is_storable', '=', True),   # ต้องเป็น storable
  ]

  ถ้า tracking = 'none' หรือ is_storable = False → สร้าง lot ไม่ได้

  Lot vs Serial ต่างกันแค่ qty

  tracking = 'lot':
    → 1 lot = หลายชิ้นได้ (qty = N)
    → เช่น: lot "JTDBR9GX10" มีน็อต 20 ตัว

  tracking = 'serial':
    → 1 serial = 1 ชิ้นเท่านั้น (qty = 1)
    → เช่น: serial "JTDBR9GX10" มีเครื่องยนต์ 1 เครื่อง

  ในบริบท Revival Vehicle ของเรา

  product.template (UK: spec + part_name + origin + condition)
    │ tracking = 'lot'
    │ is_storable = True
    │
    └→ product.product (variant)
         │
         └→ stock.lot (name = VIN)
              │ itx_vin = VIN          ← เราเพิ่มเอง
              │ itx_acquired_id        ← เราเพิ่มเอง
              │
              └→ stock.quant
                   │ quantity = จำนวนชิ้นใน lot นี้
                   │ location_id = อยู่ที่ไหนในคลัง
                   └→ ใช้ trace: lot → product → part type
                                lot → VIN → acquired → PO → cost

  สรุปง่ายๆ

  ┌──────────────────┬───────────────────┬────────────────────────┐
  │        ชั้น        │     ตอบคำถาม      │         ตัวอย่าง         │
  ├──────────────────┼───────────────────┼────────────────────────┤
  │ product.template │ อะไหล่ประเภทอะไร?  │ กันชนหน้า Civic OEM GOOD │
  ├──────────────────┼───────────────────┼────────────────────────┤
  │ product.product  │ variant (ปกติ 1:1) │ เดียวกัน                 │
  ├──────────────────┼───────────────────┼────────────────────────┤
  │ stock.lot        │ ชิ้นนี้มาจากรถคันไหน?  │ VIN: JTDBR9GX10        │
  ├──────────────────┼───────────────────┼────────────────────────┤
  │ stock.quant      │ อยู่ที่ไหน กี่ชิ้น?       │ WH/Stock, qty=2        │
  └──────────────────┴───────────────────┴────────────────────────┘

  Lot เป็นตารางแยกจาก Product ครับ ไม่ได้อยู่ใน product.template — มันเป็น instance
  tracker ที่ผูกกับ product.product อีกที