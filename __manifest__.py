# -*- coding: utf-8 -*-
{
    'name': 'ITX Revival Vehicle',
    'version': '19.0.2.0.0',
    'category': 'Inventory/Inventory',
    'summary': 'Salvage Vehicle Lifecycle Management - Assessment to ROI',
    'description': """
ITX Revival Vehicle - Salvage Vehicle Lifecycle Management
==========================================================

วงจรชีวิตซากรถ ตั้งแต่ประเมิน → ซื้อ → แตกชิ้นส่วน → ติดตาม ROI

Flow:
1. สายสืบเจอซากรถ → แจ้ง H/O
2. H/O สร้างแบบประเมิน → Generate list อะไหล่ + ราคาคาดการณ์
3. พิมพ์ Checklist ให้สายสืบไปสำรวจหน้างาน
4. H/O ตัดสินใจ: ไม่ซื้อ / ซื้อขายทั้งคัน / ซื้อแตก part
5. ถ้าซื้อ → สร้าง PO → รับเข้าสต็อก → Unbuild → อะไหล่พร้อมขาย

Features:
- Assessment: แบบประเมินซากรถ + Generate parts จาก BOM Template
- Acquired: รถที่ซื้อแล้ว + Analytic Account per vehicle
- Integration: MRP Unbuild, Purchase Order
- Reports: ROI Report per vehicle

Developed by IT Expert Training & Outsourcing Co. (Thailand)
    """,
    'author': 'IT Expert Training & Outsourcing Co.',
    'website': 'https://www.itexpert.co.th',
    'license': 'LGPL-3',
    'depends': [
        'itx_info_vehicle',
        'mrp',
        'purchase_stock',
        'account',
    ],
    'data': [
        # Security
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/ir_config_parameter_data.xml',
        # Views
        'views/itx_revival_assessment_views.xml',
        'views/itx_revival_acquired_views.xml',
        'views/itx_revival_dismantling_views.xml',
        'views/mrp_bom_views.xml',
        'views/menuitems.xml',
    ],
    'demo': [],
    'installable': True,
    'application': False,
    'auto_install': False,
}
