{
    'name': "VTC Elearning",
    'version': "1.0.0",
    'author': "Sythil Tech",
    'category': "Tools",
    'summary': "Allows users to upload videos to your website",
    'license':'LGPL-3',
    'data': [
        'data/data.xml',
        'security/ir.model.access.csv',
        'views/certificate_view.xml',
        'views/slide_slide_view_inherit.xml',
        'views/comment_view_inherit.xml',
        'views/quiz_view_inherit.xml',
        'views/lecturers_view.xml',
        'views/student_view.xml',
        'views/course_level.xml',
        'views/slide_channel_inherit.xml',
        'views/rating_system.xml',
        'views/report_view_inherit.xml',
        'views/menu_action.xml',
        'views/slide_channel_tag.xml',
        'views/product_template.xml',
        'views/upload_template.xml',
        'views/approve_request_views.xml'
    ],
    'demo': [],
    'depends': [
        'website_slides',
        'openeducat_quiz',
        'base_unit_vn',
        'rating',
        'contacts',
        'approvals'
    ],
    'images':[

    ],
    'installable': True,
}