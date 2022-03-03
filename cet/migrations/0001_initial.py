# Generated by Django 3.2 on 2021-04-28 13:33

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='Pdf_fast_v2',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('zone_code', models.CharField(max_length=1)),
                ('branche', models.CharField(max_length=1)),
                ('type_souscription', models.CharField(max_length=1)),
                ('portfolio_type', models.CharField(max_length=1)),
                ('sinistre_1', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_sin_ouv_2', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_sin_clo_3', models.DecimalField(decimal_places=2, max_digits=28)),
                ('SINISTRES_COMP_EXE_4', models.DecimalField(decimal_places=2, max_digits=28)),
                ('SINISTRES_PRIMES_ACQU_5', models.DecimalField(decimal_places=2, max_digits=28)),
                ('les_charges_6', models.DecimalField(decimal_places=2, max_digits=28)),
                ('commissions_primes_7', models.DecimalField(decimal_places=2, max_digits=28)),
                ('courtage_8', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_egal_ouv_24', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_equi_ouv_25', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_egal_clo_26', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_equi_clo_27', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_egal_clo_ouv_22', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_equi_clo_ouv_23', models.DecimalField(decimal_places=2, max_digits=28)),
                ('total_9', models.DecimalField(decimal_places=2, max_digits=28)),
                ('primes_encaiss_10', models.DecimalField(decimal_places=2, max_digits=28)),
                ('ent_prt_prime_11', models.DecimalField(decimal_places=2, max_digits=28)),
                ('sor_prt_prime_12', models.DecimalField(decimal_places=2, max_digits=28)),
                ('primes_nettes_13', models.DecimalField(decimal_places=2, max_digits=28)),
                ('primes_nettes_ann_16', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_pri_ouv_17', models.DecimalField(decimal_places=2, max_digits=28)),
                ('prov_prim_clo_18', models.DecimalField(decimal_places=2, max_digits=28)),
                ('primes_acquises_exe_19', models.DecimalField(decimal_places=2, max_digits=28)),
                ('BENEFICE_PERTE_20', models.DecimalField(decimal_places=2, max_digits=28)),
                ('rn_pra_21', models.DecimalField(decimal_places=2, max_digits=28)),
                ('wakala_22', models.DecimalField(decimal_places=2, max_digits=28)),
            ],
        ),
    ]
