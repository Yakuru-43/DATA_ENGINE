# Generated by Django 3.2 on 2021-08-02 12:05

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('cet', '0006_alter_rightssupport_options'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='rightssupport',
            options={'default_permissions': (), 'managed': False, 'permissions': (('view_ibnr', 'Acess the IBNR page'), ('management', 'Acess the management page'), ('view_prov_egal_equi', 'Acess the PROV. EGAL-EQUI page'), ('super_management', 'Acess the super management page'), ('vendor_rights', 'Global vendor rights'), ('any_rights', 'Global any rights'))},
        ),
    ]
