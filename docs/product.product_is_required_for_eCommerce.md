❯ ขอบคุณคับ พี่คลอด วิเคราะห์ข้อดีข้อ เสียของการ ใช้หรือไม่ใช้ product.variant ในงานนี้ให้ฟัง
  อย่างนักวิเคราะห์ระบบ หน่อย

● วิเคราะห์: Variant vs No-Variant ในงาน Revival Vehicle

  ---
  ทำความเข้าใจ 2 แนวทางก่อน

  แบบ A — ปัจจุบัน (No Variant: 1 template = 1 product)
  ──────────────────────────────────────────────────
  product.template: "กันชนหน้า Civic FC OEM GOOD"    → 1 product.product
  product.template: "กันชนหน้า Civic FC OEM FAIR"    → 1 product.product
  product.template: "กันชนหน้า Civic FC AFT GOOD"    → 1 product.product
  = 3 templates, 3 products


  แบบ B — ใช้ Variant (1 template = หลาย variants)
  ──────────────────────────────────────────────────
  product.template: "กันชนหน้า Civic FC"
    ├── attribute: Origin  → [OEM, AFT, USED]
    ├── attribute: Condition → [GOOD, FAIR, POOR, BROKEN]
    │
    └── variants (Origin × Condition):
         ├── product.product: OEM × GOOD
         ├── product.product: OEM × FAIR
         ├── product.product: OEM × POOR
         ├── product.product: OEM × BROKEN
         ├── product.product: AFT × GOOD
         ├── ... (3 × 4 = 12 variants)
  = 1 template, 12 products

  ---
  แบบ B — ใช้ Variant

  ┌─────┬─────────────────────┬─────────────────────────────────────────────┐
  │     │         ข้อดี         │                  รายละเอียด                  │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 1   │ Product catalog     │ 63 templates ต่อ spec (แทนที่จะเป็น 63 × N)     │
  │     │ สะอาด               │                                             │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 2   │ เปรียบเทียบ condition │ เปิด template เดียว เห็นทุก variant + stock     │
  │     │  ง่าย                │ ของแต่ละ condition                           │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 3   │ ระบบราคา Odoo       │ price_extra per variant — OEM+GOOD = +500,  │
  │     │ built-in            │ AFT+FAIR = -200                             │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 4   │ E-commerce friendly │ ลูกค้าเลือก "กันชนหน้า Civic" แล้วเลือก condition  │
  │     │                     │ ได้                                          │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 5   │ Report group by     │ ดูยอดขายรวมทุก condition ของ part เดียวกัน      │
  │     │ template            │                                             │
  └─────┴─────────────────────┴─────────────────────────────────────────────┘

  ┌─────┬──────────────────┬────────────────────────────────────────────────┐
  │     │      ข้อเสีย       │                   รายละเอียด                    │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │     │ Variant          │ 3 origin × 4 condition = 12 variants ต่อ part,  │
  │ 1   │ Explosion        │ 63 parts = 756 variants ต่อ spec                │
  │     │                  │ ส่วนใหญ่ไม่มีตัวตนจริง                               │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │ 2   │ Phantom variants │ Odoo สร้าง variant ทุกชุดค่าผสม แต่จริงๆ มีแค่ 1-2     │
  │     │                  │ condition ต่อ part ที่เจอ — ที่เหลือเป็น noise        │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │     │                  │ BOM line ผูก product.product (variant) ต้องระบุว่า │
  │ 3   │ BOM ซับซ้อน        │  OEM+GOOD ทุก line — ถ้าใช้ variant ต้อง configure │
  │     │                  │  เพิ่ม                                           │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │ 4   │ Code ต้อง         │ _get_or_create_part_product ต้องเปลี่ยนเป็น manage │
  │     │ refactor หนัก     │  attribute + variant แทน template search       │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │     │ Dismantling ปรับ  │ ตอน action_done ต้อง switch variant (ไม่ใช่สร้าง   │
  │ 5   │ condition ยาก    │ product ใหม่) — ต้องจัดการ stock move ระหว่าง      │
  │     │                  │ variant                                        │
  ├─────┼──────────────────┼────────────────────────────────────────────────┤
  │ 6   │ User สับสน        │ ช่างในคลังเห็น dropdown 12 variants ทั้งที่มีของจริงแค่  │
  │     │                  │ 2                                              │
  └─────┴──────────────────┴────────────────────────────────────────────────┘

  ---
  แบบ A — ไม่ใช้ Variant (ปัจจุบัน)

  ┌─────┬────────────────────┬──────────────────────────────────────────────┐
  │     │        ข้อดี         │                  รายละเอียด                   │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 1   │ สร้าง product       │ เจอ OEM+GOOD ก็สร้างแค่นั้น ไม่มี phantom           │
  │     │ เมื่อจำเป็นเท่านั้น      │                                              │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 2   │ Simple mental      │ 1 product = 1 สิ่งที่จับต้องได้จริง                  │
  │     │ model              │                                              │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 3   │ BOM ตรงไปตรงมา     │ BOM line → product ตรงๆ ไม่ต้องคิดเรื่อง variant  │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 4   │ Dismantling ง่าย    │ condition ต่าง = สร้าง product ใหม่ ไม่ต้อง swap  │
  │     │                    │ variant                                      │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 5   │ Lot tracking ชัด    │ 1 lot ผูก 1 product — ไม่สับสนระหว่าง variants   │
  ├─────┼────────────────────┼──────────────────────────────────────────────┤
  │ 6   │ ไม่ต้อง configure    │ ไม่ต้องสร้าง product.attribute +                │
  │     │ attribute          │ product.attribute.value + template line      │
  └─────┴────────────────────┴──────────────────────────────────────────────┘

  ┌─────┬─────────────────────┬─────────────────────────────────────────────┐
  │     │        ข้อเสีย        │                  รายละเอียด                  │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 1   │ Product templates   │ ถ้ามี 5 specs × 63 parts × 3 conditions =     │
  │     │ เยอะ                │ ~945 templates                              │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 2   │ ดูภาพรวม part ยาก    │ อยากเห็น "กันชนหน้า Civic ทุก condition" ต้อง    │
  │     │                     │ filter เอง                                  │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 3   │ ไม่มี price_extra     │ ต้องตั้งราคาแยกทุก product ไม่มี base price +     │
  │     │                     │ delta                                       │
  ├─────┼─────────────────────┼─────────────────────────────────────────────┤
  │ 4   │ E-commerce ไม่สวย    │ ลูกค้าเห็น product แยกๆ ไม่ได้เลือก condition จาก │
  │     │                     │  dropdown                                   │
  └─────┴─────────────────────┴─────────────────────────────────────────────┘

  ---
  วิเคราะห์เชิงลึก — ทำไมแบบ A เหมาะกว่าสำหรับงานนี้

  เหตุผลที่ 1: ธรรมชาติของข้อมูลไม่เหมาะกับ Variant

  Variant ออกแบบมาสำหรับ:          งานนี้คือ:
  ─────────────────────────        ──────────────────────
  ลูกค้า "เลือก" attribute         ช่าง "พบ" สภาพจริง
  ทุก combination มีขาย            ส่วนใหญ่ไม่มีตัวตน
  รู้ล่วงหน้าว่ามี variant อะไร    ไม่รู้จนกว่าจะรื้อจริง
  เสื้อ size S/M/L = ทุก size มี    OEM+BROKEN = แทบไม่เจอ

  Origin × Condition เป็น physical reality ที่ค้นพบ ไม่ใช่ configuration ที่ลูกค้าเลือก

  เหตุผลที่ 2: ตัวเลข Variant Explosion

  สมมติ:
    5 specs (Civic, Jazz, City, HRV, CRV)
    63 parts ต่อ spec
    3 origins (OEM, AFT, USED)
    4 conditions (GOOD, FAIR, POOR, BROKEN)

  แบบ A (No variant):
    สร้างตามจริง — อาจ ~200-300 products ที่มีของจริง

  แบบ B (Variant):
    5 × 63 = 315 templates
    × 12 variants = 3,780 product.product records
    แต่มีของจริงแค่ ~200-300 → 90% เป็น phantom ✗

  เหตุผลที่ 3: Flow การทำงานจริง

  Assessment:
    Generate lines → สร้าง product OEM+GOOD (default)
    → แบบ A: สร้าง template ใหม่ถ้าไม่มี (ง่าย)
    → แบบ B: ต้อง ensure attribute อยู่ใน template + สร้าง variant (ซับซ้อน)

  Dismantling (action_done):
    ช่างพบว่าจริงๆ เป็น OEM+FAIR
    → แบบ A: _get_or_create_part_product → สร้าง template ใหม่ + lot
    → แบบ B: ต้อง find correct variant จาก matrix
             + stock move จาก variant เดิมไป variant ใหม่
             + ถ้า variant ยังไม่มี ต้อง "activate" dynamic variant
             = ซับซ้อนกว่ามาก

  ---
  แบบ A ข้อเสียแก้ได้ไหม?

  ┌───────────────────┬─────────────────────────────────────────────────────┐
  │    ข้อเสียแบบ A     │               วิธีแก้โดยไม่ต้องใช้ Variant                │
  ├───────────────────┼─────────────────────────────────────────────────────┤
  │ Product templates │ ใช้ search/filter ด้วย itx_spec_id + itx_part_name_id │
  │  เยอะ             │  — Odoo filter ทำได้ดีอยู่แล้ว                           │
  ├───────────────────┼─────────────────────────────────────────────────────┤
  │ ดูภาพรวม part ยาก  │ สร้าง custom report group by part_name แสดงทุก        │
  │                   │ condition + stock                                   │
  ├───────────────────┼─────────────────────────────────────────────────────┤
  │ ไม่มี price_extra   │ ตั้ง pricelist rule ตาม condition ได้ (เช่น FAIR = -20% │
  │                   │  จาก GOOD)                                          │
  ├───────────────────┼─────────────────────────────────────────────────────┤
  │ E-commerce ไม่สวย  │ ยังไม่ถึงขั้นนั้น — ถ้าถึงค่อย evaluate อีกที                   │
  └───────────────────┴─────────────────────────────────────────────────────┘

  ---
  สรุป — คำแนะนำของผม

  ┌─────────────────────────────────────────────────────┐
  │  แบบ A (No Variant) เหมาะกับงานนี้กว่า             │
  │                                                     │
  │  เหตุผลหลัก:                                        │
  │  1. Origin/Condition = ค้นพบ ไม่ใช่ configure        │
  │  2. Variant explosion 90% เป็น phantom               │
  │  3. Dismantling flow ง่ายกว่ามาก                     │
  │  4. ข้อเสียแก้ได้ด้วย filter + report               │
  │  5. Code ปัจจุบันทำงานดีแล้ว ไม่ต้อง refactor       │
  │                                                     │
  │  เปลี่ยนไป Variant เมื่อ:                            │
  │  - จะทำ E-commerce ขายอะไหล่ online                  │
  │  - ต้องการ price matrix ตาม condition                │
  │  - มี requirement ใหม่ที่ variant ตอบได้ดีกว่า       │
  └─────────────────────────────────────────────────────┘

  ตอนนี้ยังไม่ต้องเปลี่ยนครับ — ถ้าอนาคตจะทำ E-commerce ค่อยพิจารณาอีกที มีอะไรอยากคุยเพิ่มไหมครับ


✻ Cooked for 1m 26s

❯ คิดเล่นไปว่า ถ้าเป็น e commerce เราแทนให้มาอ่าน (product.template & product.product)
    เราสร้าง คล้าย database view (query) ครอบ ทำให้เหมือน template & variant  แล้วให้
  e commerce ย้ายไปอ่านที่ view ที่เราสร้างขึ้น ได้หรือไม่


● คิดได้น่าสนใจครับ วิเคราะห์ให้เลย:

  ในทาง Technical — ทำ Database View ใน Odoo ได้

  # Odoo รองรับ SQL View Model ผ่าน _auto = False
  class ProductGroupView(models.Model):
      _name = 'itx.product.group.view'
      _auto = False  # ← ไม่สร้าง table จริง ใช้ SQL view

      def init(self):
          tools.drop_view_if_exists(self.env.cr, self._table)
          self.env.cr.execute("""
              CREATE VIEW itx_product_group_view AS (
                  SELECT
                      -- group by spec + part_name = "virtual template"
                      ROW_NUMBER() OVER () as id,
                      pt.itx_spec_id,
                      pt.itx_part_name_id,
                      pt.name,
                      COUNT(pp.id) as variant_count,
                      SUM(sq.quantity) as total_stock
                  FROM product_template pt
                  JOIN product_product pp ON pp.product_tmpl_id = pt.id
                  LEFT JOIN stock_quant sq ON sq.product_id = pp.id
                  WHERE pt.itx_is_vehicle_part = True
                  GROUP BY pt.itx_spec_id, pt.itx_part_name_id, pt.name
              )
          """)

  ทำได้ครับ สร้าง view model แบบนี้ไม่ยาก

  ---
  แต่ปัญหาคือ — website_sale ไม่ได้แค่ "อ่าน"

  สิ่งที่ E-commerce ทำกับ product.template / product.product:

  อ่าน (Read):
    ✓ แสดงสินค้า, ราคา, รูป, stock
    ← SQL View ทำได้

  เขียน (Write):
    ✗ หยิบใส่ตะกร้า  → sale.order.line ผูก product.product
    ✗ เช็ค stock     → stock.quant ผูก product.product
    ✗ คำนวณราคา      → pricelist ผูก product.template
    ✗ ชำระเงิน       → delivery ผูก product.product
    ✗ Wishlist        → ผูก product.product
    ← SQL View ทำไม่ได้ (read-only)

  หมายความว่า:

                      ┌─────────────────────┐
                      │   website_sale      │
                      │   (e-commerce)      │
                      └──────────┬──────────┘
                                 │
              ไม่ใช่แค่อ่าน ── มันเรียก ORM method ตรงๆ
              เช่น:
                product.template.browse()
                product.product._get_combination_info()
                sale.order._cart_update(product_id=...)
                stock.quant._get_available_quantity(product_id=...)
                                 │
                      ┌──────────▼──────────┐
                      │  product.template   │ ← hard-coded ทั่ว module
                      │  product.product    │
                      └─────────────────────┘

  ถ้าจะให้ e-commerce อ่าน view แทน
  = ต้อง override ทุกจุดที่เรียก product.template
  = website_sale + website_sale_stock + payment + delivery + ...
  = เท่ากับเขียน e-commerce ใหม่

  ---
  สรุป 3 ระดับความเป็นไปได้

  ระดับ 1: ทำได้เลย — Custom Catalog Page

  ไม่แตะ website_sale เลย
  สร้าง controller + page ใหม่ที่ใช้ SQL View

  หน้าเว็บ:
    /parts/civic-fc
      ├── กันชนหน้า (3 สภาพ: OEM+GOOD ฿5,000 | OEM+FAIR ฿3,500 | AFT+GOOD ฿2,000)
      ├── ไฟหน้า (2 สภาพ: ...)
      └── ...

  กดเลือก → redirect ไปหน้า product จริงของ website_sale
           → หยิบใส่ตะกร้าตามปกติ

  ข้อดี: ง่าย, ไม่ override อะไร, SQL View ใช้ได้จริง
  ข้อเสีย: UX ไม่ seamless (2 หน้า)

  ระดับ 2: ทำได้ แต่เยอะ — Override Product Page

  Override template ของ website_sale:
    /shop/<product_template> → แก้ให้ group by part_name

  แทนที่จะแสดง variant dropdown (size, color)
  → แสดง origin + condition เป็นตัวเลือก
  → เมื่อเลือก → set product.product ที่ถูกต้องใส่ตะกร้า

  ข้อดี: UX ดี, ใช้ cart/checkout ของ Odoo ได้เลย
  ข้อเสีย: override template + JS + controller พอสมควร

  ระดับ 3: ทำไม่คุ้ม — เปลี่ยน e-commerce ทั้ง module

  เปลี่ยน website_sale ทั้งหมดให้อ่าน SQL View
  = เขียน e-commerce ใหม่
  = ไม่คุ้ม ✗

  ---
  คำแนะนำ

  ตอนนี้:
    → ยังไม่ต้องทำอะไร (ยังไม่มี e-commerce requirement)

  เมื่อถึงเวลา:
    → ระดับ 1 (Custom Catalog + SQL View) ทำก่อน
    → ถ้า UX ไม่พอ ค่อยทำระดับ 2 (Override Product Page)
    → ไม่แตะระดับ 3

  SQL View ที่คิดไว้ใช้ได้จริง — แค่ใช้เป็น "หน้าร้าน"
  ส่วน "หลังร้าน" (cart, checkout, stock) ยังผูก product จริง

  ไอเดียดีครับ แค่ต้องแยกชั้น "แสดงผล" กับ "ทำธุรกรรม" ออกจากกัน — SQL View เหมาะกับชั้นแสดงผ
   ส่วนชั้นธุรกรรมยังต้องใช้ product.product จริง


✻ Worked for 54s

❯ ถ้าจะต้องแก้ A>B   ตอน  ลูกค้าใช้งานระบบไปแล้ว ยากง่ายแค่ไหน

● วิเคราะห์ Migration A→B (No Variant → Variant) ตอนมี Data จริงแล้ว

  ขนาดปัญหา — ต้อง migrate กี่ตาราง?

  ตารางที่กระทบโดยตรง:
  ─────────────────────────────────────────────────
  product_template          ← รวม templates เข้าด้วยกัน
  product_product           ← เปลี่ยนจาก 1:1 เป็น N:1
  product_template_attribute_line  ← สร้างใหม่
  product_template_attribute_value ← สร้างใหม่

  ตารางที่มี FK ชี้ไป product — ต้อง re-map ทั้งหมด:
  ─────────────────────────────────────────────────
  stock_quant               ← lot + qty ผูก product_id
  stock_lot                 ← lot ผูก product_id
  stock_move                ← ทุก stock movement
  stock_move_line           ← ทุก move detail
  sale_order_line           ← ทุกรายการขาย
  purchase_order_line       ← ทุกรายการซื้อ
  account_move_line         ← ทุกรายการบัญชี (invoice)
  mrp_bom_line              ← BOM ทุก line
  mrp_unbuild               ← unbuild orders
  itx_revival_assessment_line    ← assessment lines
  itx_revival_dismantling_line   ← dismantling lines (2 fields)

  ตัวอย่างสิ่งที่ต้องทำ

  ก่อน Migration (แบบ A):
  ═══════════════════════════════════════════════════
  product.template #101: "กันชนหน้า Civic FC OEM GOOD"
    └→ product.product #201

  product.template #102: "กันชนหน้า Civic FC OEM FAIR"
    └→ product.product #202

  product.template #103: "กันชนหน้า Civic FC AFT GOOD"
    └→ product.product #203

  stock.lot: VIN=JTDBR → product #201
  stock.quant: product #201, qty=1, location=WH/Stock
  sale.order.line: product #201, qty=1, price=5000
  account.move.line: product #201 (invoice ที่ออกไปแล้ว)


  หลัง Migration (แบบ B):
  ═══════════════════════════════════════════════════
  product.template #101: "กันชนหน้า Civic FC"    ← เหลือ 1
    ├── attribute: Origin [OEM, AFT]
    ├── attribute: Condition [GOOD, FAIR]
    ├→ product.product #201: OEM × GOOD          ← id เดิม (ห้ามเปลี่ยน!)
    ├→ product.product #202: OEM × FAIR           ← id เดิม
    └→ product.product #203: AFT × GOOD           ← id เดิม

  product.template #102 → ลบ (merge เข้า #101)
  product.template #103 → ลบ (merge เข้า #101)

  stock.lot, stock.quant, sale.order.line, account.move.line
    → product_id ยังเป็น #201 เหมือนเดิม (ไม่ต้องแก้)
    → แต่ product #201 ย้ายไปอยู่ template #101 แทน

  ขั้นตอน Migration Script

  Step 1: สร้าง Attribute + Values
  ──────────────────────────────────
    สร้าง product.attribute "Origin" → values [OEM, AFT, USED]
    สร้าง product.attribute "Condition" → values [GOOD, FAIR, POOR, BROKEN]


  Step 2: เลือก template ตัวแทน (group by spec + part_name)
  ──────────────────────────────────
    "กันชนหน้า Civic FC" มี 3 templates (#101, #102, #103)
    → เลือก #101 เป็นตัวแทน (survivor)
    → #102, #103 เป็น donor (จะถูก merge)


  Step 3: ย้าย product.product ไปอยู่ survivor template
  ──────────────────────────────────
    product #201 (อยู่ #101 อยู่แล้ว) → ไม่ต้องทำอะไร
    product #202 (อยู่ #102) → UPDATE product_tmpl_id = 101
    product #203 (อยู่ #103) → UPDATE product_tmpl_id = 101

    ⚠️  จุดอันตราย: product.product.product_tmpl_id เปลี่ยน
    → ทุก FK ที่ชี้ product_product ไม่กระทบ (ยังเป็น id เดิม)
    → แต่ FK ที่ชี้ product_template กระทบ!


  Step 4: สร้าง attribute lines บน survivor template
  ──────────────────────────────────
    template #101 + attribute "Origin" → [OEM, AFT]
    template #101 + attribute "Condition" → [GOOD, FAIR]
    + map แต่ละ product.product กับ combination ที่ถูกต้อง


  Step 5: แก้ FK ที่ชี้ product_template (donor → survivor)
  ──────────────────────────────────
    ⚠️  ตารางที่มี product_tmpl_id:
      - sale.order.line.product_template_id
      - purchase.order.line.product_template_id
      - pricelist.item
      - stock.warehouse.orderpoint
      - mrp.bom.product_tmpl_id        ← BOM!
      - website_sale (product page URLs)
      - ...อีกหลายสิบตาราง

    UPDATE ทุกตาราง SET product_tmpl_id = 101
    WHERE product_tmpl_id IN (102, 103)


  Step 6: ลบ donor templates
  ──────────────────────────────────
    DELETE product_template WHERE id IN (102, 103)

    ⚠️  ถ้ามี FK ที่ลืม update → CASCADE DELETE ข้อมูลหาย!
    ⚠️  ถ้ามี FK ที่เป็น RESTRICT → error ลบไม่ได้


  Step 7: ตรวจสอบ
  ──────────────────────────────────
    - stock.quant ยังถูกต้อง?
    - lot ยังผูก product ถูก?
    - invoice ที่ออกไปแล้วยังดูได้?
    - BOM ยังใช้ได้?
    - report ยอดขายยังตรง?

  ---
  ระดับความยาก — ขึ้นกับจังหวะเวลา

  ┌──────────────────────────┬─────────┬────────────────────────────────────┐
  │         ช่วงเวลา          │ ความยาก │               เหตุผล                │
  ├──────────────────────────┼─────────┼────────────────────────────────────┤
  │ ก่อน go-live (ไม่มี data    │ ง่าย     │ ลบ product ทิ้งหมด สร้างใหม่           │
  │ จริง)                     │         │                                    │
  ├──────────────────────────┼─────────┼────────────────────────────────────┤
  │ เพิ่ง go-live (data น้อย,   │ ปานกลาง │ migrate ได้ แต่ต้อง test หนัก          │
  │ ยังไม่มี invoice)           │         │                                    │
  ├──────────────────────────┼─────────┼────────────────────────────────────┤
  │ ใช้งานแล้ว 6 เดือน (มี SO,   │ ยาก     │ FK กระจายทุกตาราง, ห้ามพลาด          │
  │ invoice, stock move)     │         │                                    │
  ├──────────────────────────┼─────────┼────────────────────────────────────┤
  │ ใช้งานแล้ว 1+ ปี (data      │ ยากมาก  │ migration script ซับซ้อน, downtime   │
  │ เยอะ, มี custom report)   │         │ นาน, ต้อง audit ทุก report           │
  └──────────────────────────┴─────────┴────────────────────────────────────┘

  ---
  ความเสี่ยงหลัก

  1. ข้อมูลบัญชีเสียหาย
     ──────────────────
     account.move.line ผูก product_id
     ถ้า product ถูก merge ผิด → งบการเงินผิด
     invoice ที่ออกไปแล้ว → ลูกค้าเปิดดูแล้วเห็น product ผิด
     ⚠️  ผู้สอบบัญชีไม่ยอม

  2. Stock ไม่ตรง
     ──────────────
     stock.quant ผูก product_id (ไม่ใช่ template)
     → ถ้า product_id ไม่เปลี่ยน ก็ปลอดภัย
     → แต่ถ้า Odoo recalculate stock จาก template → อาจผิด

  3. Lot traceability ขาด
     ─────────────────────
     lot → product → template chain เปลี่ยน
     report ที่ group by template → ผลลัพธ์เปลี่ยน

  4. URL / Bookmark หาย (ถ้ามี e-commerce)
     ──────────────────────────────────────
     /shop/product-102 → ลบไปแล้ว → 404

  ---
  สรุป

  ┌──────────────────────────────────────────────────────┐
  │                                                      │
  │  A→B ตอนมี data จริง = ทำได้ แต่เจ็บตัว              │
  │                                                      │
  │  เหมือนเปลี่ยนเครื่องยนต์ตอนรถวิ่งอยู่               │
  │  ไม่ใช่แค่ product table — กระทบทุก module            │
  │  ที่มี FK ชี้ product_template                        │
  │                                                      │
  │  ยิ่งใช้นาน ยิ่ง migrate ยาก                          │
  │  ยิ่งมี invoice/บัญชี ยิ่งเสี่ยง                       │
  │                                                      │
  │  คำแนะนำ:                                             │
  │  ตัดสินใจก่อน go-live ว่าจะ A หรือ B                  │
  │  ถ้าเลือก A แล้ว → อยู่กับ A                          │
  │  ถ้าต้องการ e-commerce → ใช้วิธี Custom Catalog       │
  │  (SQL View หน้าร้าน + product จริงหลังร้าน)           │
  │                                                      │
  └──────────────────────────────────────────────────────┘

  เป็นเหตุผลสำคัญที่สนับสนุนว่า เลือก A แล้วอยู่กับ A ดีกว่า — ถ้าอนาคตต้องการหน้าร้านสวยๆ ใช้ SQL
  View ครอบด้านหน้าแทนครับ

✻ Sautéed for 1m 0s



มีแนวโน้ม ใช้ ecommerce เราต้องใช้ product.product ตอนนี้เลย   มีทางมั๊ย ไม่ให้  odoo แตก
   variant  เป็ฯ 12 เอง originxcondition  (เราสร้างเอง variant เอง เท่าที่ใช้พอ)

● ได้ครับ! Odoo รองรับเรื่องนี้อยู่แล้ว ให้ผมเช็ค source code ก่อน

  Searched for 1 pattern, read 1 file (ctrl+o to expand)

● มีทางครับ! Odoo มี setting ตรงนี้เลย

  Variant Creation Mode — 3 แบบ

  product.attribute.create_variant:

    'always'    — สร้างทุก combination ทันที (3×4 = 12)     ← ไม่เอา
    'dynamic'   — สร้างเมื่อมีคนเลือกใน SO/ecommerce       ← ตัวนี้!
    'no_variant' — ไม่สร้าง variant เลย

  dynamic คือคำตอบ

  ตั้ง attribute "Origin" → create_variant = 'dynamic'
  ตั้ง attribute "Condition" → create_variant = 'dynamic'

  ผลลัพธ์:
  ──────────────────────────────────────────────
  product.template: "กันชนหน้า Civic FC"
    ├── attribute: Origin [GEN, OEM, AFT]
    ├── attribute: Condition [NNEW, GOOD, FAIR, POOR]
    │
    └── product.product: ยังไม่สร้าง! (0 variants)

  เมื่อ dismantling เจอจริงว่าเป็น GEN+GOOD:
    → code สร้าง variant GEN×GOOD ← 1 variant

  เมื่อรถคันถัดไป เจอ GEN+FAIR:
    → code สร้าง variant GEN×FAIR ← 2 variants

  ใช้ไป 1 ปี อาจมีแค่ 3-4 variants จาก 12 ที่เป็นไปได้

  เปรียบเทียบ

  ┌───────────────┬──────────────┬─────────────────────────┬───────────────┐
  │               │    always    │         dynamic         │  no_variant   │
  ├───────────────┼──────────────┼─────────────────────────┼───────────────┤
  │ สร้าง variant  │ เพิ่ม          │ มีคนเลือก/code สร้าง       │ ไม่สร้างเลย     │
  │ เมื่อ           │ attribute ปุ๊บ │                         │               │
  ├───────────────┼──────────────┼─────────────────────────┼───────────────┤
  │ จำนวน variant │ ครบทุก combo  │ เท่าที่ใช้จริง (2-4)         │ 0             │
  │               │ (12)         │                         │               │
  ├───────────────┼──────────────┼─────────────────────────┼───────────────┤
  │ E-commerce    │ dropdown     │ dropdown เห็นทุกตัว แต่     │ ไม่มี variant   │
  │               │ เห็นทุกตัว      │ stock=0 ถ้ายังไม่สร้าง      │ ให้เลือก        │
  ├───────────────┼──────────────┼─────────────────────────┼───────────────┤
  │ เหมาะกับงานนี้   │ ไม่เหมาะ      │ เหมาะที่สุด                │ ไม่เหมาะ       │
  └───────────────┴──────────────┴─────────────────────────┴───────────────┘

  แต่มีจุดที่ต้องเปลี่ยน code

  ปัจจุบัน _get_or_create_part_product สร้าง product.template ใหม่ ทุกครั้งที่เจอ combo
  ใหม่ ถ้าจะใช้ variant ต้องเปลี่ยนเป็น:

  # แบบ A (ปัจจุบัน):
  #   เจอ GEN+GOOD → สร้าง template "กันชนหน้า Civic FC GEN GOOD"
  #   เจอ GEN+FAIR → สร้าง template "กันชนหน้า Civic FC GEN FAIR"
  #   = 2 templates, 2 products

  # แบบ B (variant + dynamic):
  #   เจอ GEN+GOOD → หา template "กันชนหน้า Civic FC"
  #                 → สร้าง variant GEN×GOOD
  #   เจอ GEN+FAIR → หา template เดิม
  #                 → สร้าง variant GEN×FAIR
  #   = 1 template, 2 products

  สรุป

  ┌──────────────────────────────────────────────────┐
  │                                                  │
  │  ใช้ create_variant = 'dynamic'                  │
  │  → Odoo ไม่แตก 12 variants เอง                   │
  │  → เราสร้างเองเท่าที่เจอจริง                      │
  │  → E-commerce พร้อมใช้ (variant dropdown)         │
  │  → ไม่มี phantom product                         │
  │                                                  │
  │  แต่ต้องตัดสินใจตอนนี้:                            │
  │  ยังใช้แบบ A (ง่าย, ไม่มี variant)                │
  │  หรือเปลี่ยนเป็น B+dynamic ตอนนี้เลย?            │
  │                                                  │
  │  ถ้าจะเปลี่ยน → ทำก่อน go-live ง่ายที่สุด         │
  │  ถ้ารอหลัง go-live → migration เจ็บตัว            │
  │                                                  │
  └──────────────────────────────────────────────────┘

  จะให้วิเคราะห์ต่อว่าถ้าเปลี่ยนเป็น B+dynamic ตอนนี้ต้องแก้ code ตรงไหนบ้างไหมครับ?