from django.db import models

# Create your models here.
class Pdf_fast_takaful(models.Model):
    zone_code = models.CharField(max_length=1)
    branche = models.CharField(max_length=1)
    type_souscription = models.CharField(max_length=1)
    portfolio_type = models.CharField(max_length=1)
    sinistre_1 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_sin_ouv_2  = models.DecimalField(max_digits=28,decimal_places=2)
    prov_sin_clo_3 = models.DecimalField(max_digits=28,decimal_places=2)
    SINISTRES_COMP_EXE_4 = models.DecimalField(max_digits=28,decimal_places=2)
    SINISTRES_PRIMES_ACQU_5 = models.DecimalField(max_digits=28,decimal_places=2)
    les_charges_6 = models.DecimalField(max_digits=28,decimal_places=2)
    commissions_primes_7 = models.DecimalField(max_digits=28,decimal_places=2)
    courtage_8 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_ouv_24 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_ouv_25 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_clo_26 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_clo_27 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_clo_ouv_22 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_clo_ouv_23 = models.DecimalField(max_digits=28,decimal_places=2)
    total_9 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_encaiss_10 = models.DecimalField(max_digits=28,decimal_places=2)
    ent_prt_prime_11 = models.DecimalField(max_digits=28,decimal_places=2)
    sor_prt_prime_12 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_nettes_13 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_nettes_ann_16 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_pri_ouv_17 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_prim_clo_18 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_acquises_exe_19 = models.DecimalField(max_digits=28,decimal_places=2)
    BENEFICE_PERTE_20 = models.DecimalField(max_digits=28,decimal_places=2)
    rn_pra_21 = models.DecimalField(max_digits=28,decimal_places=2)
    wakala_22 = models.DecimalField(max_digits=28,decimal_places=2)

class Pdf_fast_v2(models.Model):
    zone_code = models.CharField(max_length=1)
    branche = models.CharField(max_length=1)
    type_souscription = models.CharField(max_length=1)
    portfolio_type = models.CharField(max_length=1)
    sinistre_1 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_sin_ouv_2  = models.DecimalField(max_digits=28,decimal_places=2)
    prov_sin_clo_3 = models.DecimalField(max_digits=28,decimal_places=2)
    SINISTRES_COMP_EXE_4 = models.DecimalField(max_digits=28,decimal_places=2)
    SINISTRES_PRIMES_ACQU_5 = models.DecimalField(max_digits=28,decimal_places=2)
    les_charges_6 = models.DecimalField(max_digits=28,decimal_places=2)
    commissions_primes_7 = models.DecimalField(max_digits=28,decimal_places=2)
    courtage_8 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_ouv_24 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_ouv_25 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_clo_26 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_clo_27 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_egal_clo_ouv_22 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_equi_clo_ouv_23 = models.DecimalField(max_digits=28,decimal_places=2)
    total_9 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_encaiss_10 = models.DecimalField(max_digits=28,decimal_places=2)
    ent_prt_prime_11 = models.DecimalField(max_digits=28,decimal_places=2)
    sor_prt_prime_12 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_nettes_13 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_nettes_ann_16 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_pri_ouv_17 = models.DecimalField(max_digits=28,decimal_places=2)
    prov_prim_clo_18 = models.DecimalField(max_digits=28,decimal_places=2)
    primes_acquises_exe_19 = models.DecimalField(max_digits=28,decimal_places=2)
    BENEFICE_PERTE_20 = models.DecimalField(max_digits=28,decimal_places=2)
    rn_pra_21 = models.DecimalField(max_digits=28,decimal_places=2)

class KRI_PART_ENGAGEMENT_SECU(models.Model) :
    security_code = models.CharField(max_length=9)
    broker_cedant_name = models.CharField(max_length=50)
    engagements = models.DecimalField(max_digits=28,decimal_places=2)
    class Meta:
        managed = False 
class KRI_RISQUE_DEFAUT(models.Model) :
    cedant_code = models.CharField(max_length=9)
    cedant_name = models.CharField(max_length=50)
    risque_defaut = models.DecimalField(max_digits=28,decimal_places=2)
    class Meta:
        managed = False 

class segmentsCna(models.Model) : 
    cna_order = models.DecimalField(max_digits=10,decimal_places=0,blank=False)
    name = models.CharField(max_length=50 ,blank=False)
    is_total = models.CharField(max_length=1 ,blank=False ,choices= [("Y", "Y"), ("N", "N"),])


class RightsSupport(models.Model):   
    class Meta:
        managed = False  # No database table creation or deletion  \
                         # operations will be performed for this model.     
        default_permissions = () # disable "add", "change", "delete"
                                 # and "view" default permissions
        permissions = ( 
            ('view_ibnr', 'Acess the IBNR page'),
            ('management','Acess the management page'),   
            ('view_prov_egal_equi','Acess the PROV. EGAL-EQUI page'),   
            ('super_management','Acess the super management page'),
            ('need_ch_pass','Check if you need to change password'),

            ('vendor_rights', 'Global vendor rights'), 
            ('any_rights', 'Global any rights'), 
        )