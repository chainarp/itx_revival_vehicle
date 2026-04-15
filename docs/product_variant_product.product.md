ภาพรวม A→B+Dynamic: สิ่งที่ต้องเปลี่ยน

  แบบ A (ปัจจุบัน):
    product.template = spec + part_name + originw+tconditionrr(UKi4gตัว)aude's
    product.product  = 1:1 กับ template (ไม่มี variant)

  แบบ B+Dynamic:
    product.template = spec + part_name                       (UK 2 ตัว)
    product.product  = variant จาก attribute Origin × Condition
    attribute create_variant = 'dynamic' (สร้างเมื่อใช้จริง)

  ---
  Module 1: itx_info_vehicle (Master Data)

  งาน 1.1 — product.template ลบ origin/condition ออกจาก template level

  # ปัจจุบัน (product_template.py):
    itx_part_origin_id  → อยู่บน product.template  ← ต้องย้ายไป attribute
    itx_condition_id    → อยู่บน product.template  ← ต้องย้ายไป attribute

  # เปลี่ยนเป็น:
    ลบ itx_part_origin_id ออกจาก product.template
    ลบ itx_condition_id ออกจาก product.template
    (ย้ายไปเป็น product.attribute + product.template.attribute.line)

  งาน 1.2 — Unique Constraint เปลี่ยน

  # ปัจจุบัน: UK = (spec, part_name, origin, condition) บน product.template
  # เปลี่ยนเป็น: UK = (spec, part_name) บน product.template
  #             origin × condition อยู่ใน variant (Odoo จัดการ unique เอง)

  # _check_vehicle_part_required_and_unique():
  #   ลบ origin/condition ออกจาก required check
  #   ลบ origin/condition ออกจาก unique domain
  #   เหลือแค่ unique (spec, part_name)

  งาน 1.3 — สร้าง Attribute master data (data XML)

  <!-- data/product_attribute_data.xml -->
  <record id="attr_part_origin" model="product.attribute">
      <field name="name">Part Origin</field>
      <field name="create_variant">dynamic</field>    <!-- สำคัญ! -->
      <field name="display_type">radio</field>
  </record>

  <record id="attr_part_condition" model="product.attribute">
      <field name="name">Part Condition</field>
      <field name="create_variant">dynamic</field>    <!-- สำคัญ! -->
      <field name="display_type">radio</field>
  </record>

  <!-- Attribute Values — map จาก master data เดิม -->
  <record id="attr_val_origin_gen" model="product.attribute.value">
      <field name="attribute_id" ref="attr_part_origin"/>
      <field name="name">Genuine</field>
      <field name="sequence">1</field>
  </record>
  <record id="attr_val_origin_oem" model="product.attribute.value">
      <field name="attribute_id" ref="attr_part_origin"/>
      <field name="name">OEM</field>
      <field name="sequence">2</field>
  </record>
  <record id="attr_val_origin_aft" model="product.attribute.value">
      <field name="attribute_id" ref="attr_part_origin"/>
      <field name="name">Aftermarket</field>
      <field name="sequence">3</field>
  </record>

  <!-- Condition Values -->
  <record id="attr_val_cond_nnew" model="product.attribute.value">
      <field name="attribute_id" ref="attr_part_condition"/>
      <field name="name">Near New</field>
      <field name="sequence">1</field>
  </record>
  <!-- ... GOOD, FAIR, POOR -->

  งาน 1.4 — เพิ่ม helper: ผูก attribute เข้า template + สร้าง variant

  # ใหม่: helper method สำหรับ product.template
  def _ensure_vehicle_part_attributes(self):
      """ผูก Origin + Condition attributes เข้า template (ถ้ายังไม่มี)"""

  def _get_or_create_variant(self, origin_value, condition_value):
      """สร้าง dynamic variant สำหรับ origin × condition ที่ระบุ
      Return: product.product
      """

  งาน 1.5 — Mapping: origin/condition master data ↔ attribute values

  ต้องตัดสินใจ:

  ทางเลือก A: ใช้ product.attribute.value เป็น master (ลบ model เดิม)
    - ลบ itx.info.vehicle.part.origin
    - ลบ itx.info.vehicle.part.condition
    - ใช้ product.attribute.value แทน
    ข้อดี: ไม่ duplicate data
    ข้อเสีย: attribute value มีแค่ name กับ sequence
             ไม่มี code, abbr, desc เหมือน model เดิม

  ทางเลือก B: เก็บทั้งคู่ + mapping field ★แนะนำ★
    - เก็บ itx.info.vehicle.part.origin ไว้ (code, abbr, desc)
    - เก็บ itx.info.vehicle.part.condition ไว้
    - เพิ่ม field: attribute_value_id → ชี้ไป product.attribute.value
    ข้อดี: เก็บ metadata ได้, ใช้ abbr ใน default_code ได้
    ข้อเสีย: ต้อง sync 2 ที่

  งาน 1.6 — default_code ปรับ format

  # ปัจจุบัน: BRAND-MODEL-GEN-SPEC-CAT-PART-SEQ (template level)
  # ไม่มี origin/condition ใน default_code

  # ต้องตัดสินใจ:
  # product.template default_code = BRAND-MODEL-GEN-SPEC-CAT-PART-SEQ (เหมือนเดิม)
  # product.product  variant suffix = Origin-Condition (Odoo จัดการผ่าน attribute)
  #   เช่น: HON-CIV-FC-1.8S-ENG-HLT-00001 (GEN, GOOD)
  #                                          ^^^^^^^^^ Odoo แสดงเป็น variant name

  งาน 1.7 — BOM Template (template_bom.py) ปรับ

  # ปัจจุบัน:
  #   default_part_origin_id → itx.info.vehicle.part.origin
  #   default_part_condition_id → itx.info.vehicle.part.condition

  # ถ้าเลือกทางเลือก B (เก็บทั้งคู่): ไม่ต้องเปลี่ยน
  # ใช้ mapping ตอน generate lines

  สรุปงาน itx_info_vehicle

  ┌─────┬─────────────────────────┬──────┬──────────────────────────────────┐
  │  #  │           งาน           │ ขนาด │               ไฟล์                │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.1 │ ลบ origin/condition จาก │ เล็ก  │ product_template.py              │
  │     │  product.template       │      │                                  │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.2 │ เปลี่ยน UK constraint เป็น │ เล็ก  │ product_template.py              │
  │     │  (spec, part_name)      │      │                                  │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.3 │ สร้าง attribute master   │ เล็ก  │ data/product_attribute_data.xml  │
  │     │ data XML                │      │ (ใหม่)                            │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.4 │ Helper: ผูก attribute +  │ กลาง │ product_template.py              │
  │     │ สร้าง dynamic variant    │      │                                  │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │     │ Mapping                 │      │ part_origin.py,                  │
  │ 1.5 │ origin/condition ↔      │ เล็ก  │ part_condition.py                │
  │     │ attribute values        │      │                                  │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.6 │ ปรับ default_code (ไม่รวม │ เล็ก  │ product_template.py              │
  │     │  origin/condition)      │      │                                  │
  ├─────┼─────────────────────────┼──────┼──────────────────────────────────┤
  │ 1.7 │ BOM Template ตรวจสอบ    │ เล็ก  │ template_bom.py                  │
  │     │ compatibility           │      │                                  │
  └─────┴─────────────────────────┴──────┴──────────────────────────────────┘

  ---
  Module 2: itx_revival_vehicle (Business Logic)

  งาน 2.1 — Assessment: _get_or_create_part_product เขียนใหม่

  # ปัจจุบัน (itx_revival_assessment.py):
  def _get_or_create_part_product(self, part_template, origin, condition):
      # search product.template ด้วย UK 4 ตัว
      # ถ้าไม่เจอ → สร้าง template ใหม่
      # return template.product_variant_id

  # เปลี่ยนเป็น:
  def _get_or_create_part_product(self, part_template, origin, condition):
      # Step 1: หา product.template ด้วย UK 2 ตัว (spec, part_name)
      #         ถ้าไม่เจอ → สร้าง template ใหม่
      # Step 2: ผูก attributes (Origin + Condition) เข้า template
      # Step 3: สร้าง dynamic variant สำหรับ origin × condition
      # return product.product (variant)

  งาน 2.2 — Assessment: _get_or_create_salvage_product ปรับ

  # เหมือน 2.1 — ซากรถก็เป็น variant (SALVAGE + OEM + GOOD)
  # สร้าง template "Salvage Vehicle Civic FC"
  # สร้าง variant OEM × GOOD

  งาน 2.3 — Assessment: _get_or_create_spec_bom ปรับ BOM line

  # BOM line ผูก product.product (variant) ไม่ใช่ template
  # ต้องแน่ใจว่า bom_line.product_id = variant ที่ถูกต้อง
  # ปัจจุบันทำถูกแล้ว (product_id = product.product)
  # แค่ต้องแน่ใจว่า _get_or_create_part_product return variant

  งาน 2.4 — Dismantling: _get_or_create_part_product เขียนใหม่

  # ปัจจุบัน (itx_revival_dismantling.py):
  def _get_or_create_part_product(self, part_template, origin, condition):
      # เหมือน assessment — search template + สร้าง template ใหม่

  # เปลี่ยนเป็น:
      # Step 1: หา template ด้วย (spec, part_name)
      # Step 2: สร้าง variant origin × condition (dynamic)
      # return product.product

  งาน 2.5 — Dismantling: action_done ปรับ

  # ปัจจุบัน:
  #   ถ้า actual ≠ assessed → สร้าง product ใหม่ (template ใหม่)
  #
  # เปลี่ยนเป็น:
  #   ถ้า actual ≠ assessed → สร้าง variant ใหม่ (บน template เดิม!)
  #   ← ง่ายกว่าเดิมด้วยซ้ำ เพราะ template เดียวกัน

  งาน 2.6 — Assessment line: product_id ยังผูก product.product

  # assessment_line.product_id → product.product (variant)
  # ไม่ต้องเปลี่ยน field definition
  # แต่ต้องแน่ใจว่า generate lines ส่ง variant ไม่ใช่ template

  สรุปงาน itx_revival_vehicle

  ┌─────┬────────────────────────────────┬──────┬────────────────────────────┐
  │  #  │              งาน               │ ขนาด │            ไฟล์             │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │     │ Assessment:                    │      │                            │
  │ 2.1 │ _get_or_create_part_product    │ กลาง │ itx_revival_assessment.py  │
  │     │ ใหม่                            │      │                            │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │     │ Assessment:                    │      │                            │
  │ 2.2 │ _get_or_create_salvage_product │ เล็ก  │ itx_revival_assessment.py  │
  │     │  ปรับ                           │      │                            │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │ 2.3 │ Assessment: BOM line ตรวจสอบ   │ เล็ก  │ itx_revival_assessment.py  │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │     │ Dismantling:                   │      │                            │
  │ 2.4 │ _get_or_create_part_product    │ กลาง │ itx_revival_dismantling.py │
  │     │ ใหม่                            │      │                            │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │ 2.5 │ Dismantling: action_done ปรับ   │ เล็ก  │ itx_revival_dismantling.py │
  │     │ logic                          │      │                            │
  ├─────┼────────────────────────────────┼──────┼────────────────────────────┤
  │ 2.6 │ Assessment line ตรวจสอบ        │ เล็ก  │ itx_revival_assessment.py  │
  └─────┴────────────────────────────────┴──────┴────────────────────────────┘

  ---
  จุดตัดสินใจสำคัญก่อนเริ่มทำ

  ต้องตอบ 3 คำถามนี้ก่อนครับ:

  คำถาม 1: Origin/Condition master data — ลบหรือเก็บ?

  ทางเลือก A: ลบ model เดิม ใช้ attribute value แทน
    ✓ ไม่ duplicate
    ✗ ไม่มี code, abbr → กระทบ default_code, lot name, report

  ทางเลือก B: เก็บทั้งคู่ + mapping ★แนะนำ★
    ✓ เก็บ code/abbr ไว้ใช้
    ✓ BOM template ไม่ต้องเปลี่ยน
    ✗ ต้อง sync attribute_value ↔ master record

  ทางเลือก C: เก็บ model เดิม เพิ่ม field ใน attribute value ★ทางเลือกที่ดีที่สุด★
    ✓ inherit product.attribute.value เพิ่ม itx_origin_id / itx_condition_id
    ✓ Odoo variant ทำงานปกติ + เรา trace กลับ master ได้
    ✗ เพิ่ม inherit อีก 1 model

  คำถาม 2: 1 template per spec+part_name หรือ 1 template per part_name (ข้าม spec)

  ทางเลือก A: 1 template = spec + part_name ★แนะนำ★
    template: "กันชนหน้า Civic FC"    ← แยก spec
    template: "กันชนหน้า Jazz GK"    ← คนละ template
    ✓ แยก BOM, แยก stock, แยก pricing ตาม spec
    ✓ ใกล้เคียง design ปัจจุบัน

  ทางเลือก B: 1 template = part_name (spec เป็น attribute เพิ่ม)
    template: "กันชนหน้า"
    variants: Civic×OEM×GOOD, Jazz×OEM×GOOD, ...
    ✗ variant explosion รุนแรงมาก (spec × origin × condition)
    ✗ ต่าง spec ราคาต่างกันมาก — ไม่เหมาะเป็น variant

  คำถาม 3: Assessment line ผูก product.product (variant) ตรงๆ เหมือนเดิม?

  ใช่ — ไม่ต้องเปลี่ยน
  assessment_line.product_id = product.product (variant GEN×GOOD)
  dismantling_line.product_id = product.product (variant เดิม)
  dismantling_line.actual_product_id = product.product (variant ใหม่ ถ้า condition
   ต่าง)

  variant เปลี่ยนแค่วิธีสร้าง ไม่เปลี่ยนวิธีใช้

  ---
  Timeline ประเมิน

  itx_info_vehicle:  งาน 1.1-1.7  ≈ 1 วัน
  itx_revival_vehicle: งาน 2.1-2.6 ≈ 1 วัน
  Testing + debug:                  ≈ 1 วัน
  ────────────────────────────────────────
  รวม ≈ 3 วัน (ก่อน go-live ไม่มี data จริง)

  ตอบ 3 คำถามข้างบนก่อนได้เลยครับ แล้วผมจะเริ่ม implement ให้!