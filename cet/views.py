import io ,os 
import decimal
import time
import datetime as datetimecomparaison
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.conf import settings
from datetime import datetime, date
from django.shortcuts import render , redirect
from cet.models import Pdf_fast_takaful , Pdf_fast_v2 , segmentsCna
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from reportlab.platypus import PageBreak , Image
from reportlab.lib.pagesizes import letter, landscape , A4 , portrait
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.pdfmetrics import registerFont
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.colors import Color, black, blue, red
from django.contrib.auth.models import Group
from django.contrib import messages
from django.db import connection , connections
import cx_Oracle
from django.contrib.auth import authenticate , logout , login
from django.contrib.auth.decorators import login_required , permission_required
from django.contrib.auth.models import Permission
from django.views.generic import View
import xlsxwriter
from django.http import HttpResponse , HttpResponseRedirect
from json import dumps
from django.http import JsonResponse
from django.contrib.auth.models import User
import pandas as pd
import numpy as np
import chainladder as cl
import json
from  django.contrib.auth.forms import PasswordChangeForm
from  django.contrib.auth.views import PasswordChangeView
from cet.forms import segmentsCnaForm
from django.views.generic import *

class PasswordsChangeView (PasswordChangeView) :
    form_class = PasswordChangeForm
    success_url = '/cet/password_change_done'

#JUST FOR TESTING PURPOSES
def test02(request) :  
    form = segmentsCnaForm()
    context = {
        'form' : form
    }
    return render(request, 'main/templates/cna_param.html', context)

def get_segments_branches (request):
    if request.method == 'GET':
        id = request.GET.get('id')
    liste_branches_cna = []
    with connection.cursor() as cursor :
        cursor.execute("""SELECT    sc.NAME ,
                                    bc2.BRANCH_NAME ,
                                    bc2.BRANCH_GROUP_CODE
                            FROM dmy.branches_cna bc
                            JOIN dop.BRANCHES_CET bc2 ON bc2.BRANCH_GROUP_CODE = bc.BRANCH_GROUP_CODE
                            JOIN dmy.CET_SEGMENTSCNA sc ON sc.ID = bc.SEGMENT_CNA_ID 
                            WHERE bc.SEGMENT_CNA_ID =   %s """,[id])
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(str(cell_data))
            liste_branches_cna.append(liste1)
    liste_branches = get_branches_cet("classique")
    liste_branches.pop(0)#POUR ENELEVER  TOUTES BRANCHES
    responseData = {
        'liste_branches_cna' : liste_branches_cna,
        'id' : id ,
        'liste_branches' : liste_branches ,
    }
    return JsonResponse(responseData)

def segments_update(request):
    if request.method == 'GET':
        id = request.GET.get('id')
        col_mod = request.GET.get('col_mod')
        new_val = request.GET.get('new_val')

    with connection.cursor() as cursor :
        if col_mod == 'order' :
            cursor.execute('update CET_SEGMENTSCNA cs set cs.CNA_ORDER = %s where cs.id = %s',[int(new_val),id])
        if col_mod == 'name' :
            cursor.execute("update CET_SEGMENTSCNA cs set cs.NAME = %s where cs.id = %s",[new_val,id])
        if col_mod == 'is_total' :
            cursor.execute("update CET_SEGMENTSCNA cs set cs.IS_TOTAL = %s where cs.id = %s",[new_val,id])
    responseData = {
        'erreur' : '0' ,
    }
    return JsonResponse(responseData)

def segments_delete(request):
    if request.method == 'GET':
        id = request.GET.get('id')

    with connection.cursor() as cursor :
        cursor.execute("delete from CET_SEGMENTSCNA x where x.id = %s",[int(id)])
        cursor.execute("DELETE FROM dmy.BRANCHES_CNA bc WHERE bc.SEGMENT_CNA_ID =%s",[int(id)])
    responseData = {
        'erreur' : '0' ,
    }
    return JsonResponse(responseData)

def segments_br_add(request):
    erreur_code = 0
    erreur_msg=''
    if request.method == 'GET':
        id = request.GET.get('id_seg')
        code_br = request.GET.get('code_br')
    with connection.cursor() as cursor :
        cursor.execute("SELECT * FROM dmy.BRANCHES_CNA bc WHERE bc.SEGMENT_CNA_ID = %s AND bc.BRANCH_GROUP_CODE = %s",[int(id),code_br])
        row = cursor.fetchone()

        if row:
            erreur_code = 1
            erreur_msg ="Cette branche existe déja dans ce segment"

        else : 
            cursor.execute("insert into dmy.BRANCHES_CNA bc values (%s,%s)",[int(id),code_br])

        cursor.execute("SELECT bc2.BRANCH_NAME FROM dop.BRANCHES_CET bc2 WHERE bc2.BRANCH_GROUP_CODE = %s",[code_br])
        row = cursor.fetchone()
        name_branche = row[0]
    responseData = {
        'id' : id ,
        'code_br' : code_br ,
        'erreur' : erreur_code ,
        'erreur_msg' : erreur_msg,
        'name_branche' : name_branche
    }
    return JsonResponse(responseData)

class ReviewsListView(ListView):
    template_name = 'main/templates/cna_param.html'
    model = segmentsCna
    context_object_name = "reviews"

class Reviewview(CreateView):
    model = segmentsCna
    form_class = segmentsCnaForm
    template_name = 'main/templates/cna_param.html'
    success_url = '/cet/test'

    def get_context_data(self, **kwargs):
        kwargs['liste_cna'] = segmentsCna.objects.order_by('cna_order')
        return super(Reviewview, self).get_context_data(**kwargs)

def authentification(request) : 
    compte = ''
    mdp =''
    if request.method == 'POST':
        compte = request.POST.get('compte')
        mdp = request.POST.get('mdp')
    compteNormalise = compte.lower()
    user = authenticate(username=compteNormalise, password=mdp)
    if user is not None:
        login(request, user)
        #return render(request, 'main/templates/index.html')
        return HttpResponseRedirect('/cet')
    else :
        messages.error(request ,'Compte ou mot de passe incorrect')
        context = {
        'error' : 1,
         }
        return render(request, 'main/templates/login.html', context)

def login_redirect(request) : 
    return render(request, 'main/templates/login.html')

@login_required
def save_taux_egal_equi(request):
    if request.method == 'GET':
        taux_grele = request.GET.get('taux_grele')
        taux_vie = request.GET.get('taux_vie')
        taux_credit = request.GET.get('taux_credit')

    with connection.cursor() as cursor :
        cursor.execute("DELETE FROM  DMY.CET_TAUX_EGAL_EQUI x WHERE x.NUM_CET =  (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)")
        cursor.execute("INSERT INTO DMY.CET_TAUX_EGAL_EQUI VALUES ((SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp),%s,%s,%s)",[taux_vie,taux_grele,taux_credit])
    context = {
        'taux_grele' : taux_grele ,
        'taux_vie' : taux_vie ,
        'taux_credit' : taux_credit ,
    }
    return render(request, 'main/templates/egal_equi.html' , context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')# IS USED TO FORCE CHANGE OF PASSWORD
@permission_required('cet.view_prov_egal_equi' ,raise_exception =True)
def view_egal_equi(request) :
    with connection.cursor() as cursor :
        cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        cursor.execute("SELECT * FROM  DMY.CET_TAUX_EGAL_EQUI x WHERE x.NUM_CET =  (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)")
        row1 = cursor.fetchone()
        #We use Strings and replace , with . so that the numbers whill display correctly in CHROME 
        if row1 :

            taux_vie = str(row1[1]).replace(',','.')
            taux_grele = str(row1[2]).replace(',','.')
            taux_credit = str(row1[3]).replace(',','.')
        else : 
            taux_vie = 0
            taux_grele = 0
            taux_credit = 0
    context = {
        'periode' : data ,
        'taux_vie' : taux_vie ,
        'taux_grele' : taux_grele ,
        'taux_credit' : taux_credit ,
    }
    return render(request, 'main/templates/egal_equi.html' , context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.view_prov_egal_equi' ,raise_exception =True)
def apercu_prov_egal_equi(request): 
    #GENERATES A PDF WITH THE IBNR 
    type_souscriptions = ['A','R','N']
    zones = ['1','2','3','4','*','?']

    branches = get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    year = ''
    registerFont(TTFont('Calibri', 'Calibri.ttf')) # Just some font imports
    registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
    registerFont(TTFont('Arial', 'Arial.ttf')) 
    registerFont(TTFont('Georgia', 'Georgia.ttf')) 
    registerFont(TTFont('Verdana', 'Verdana.ttf')) 
    registerFont(TTFont('Tahoma', 'Tahoma.ttf'))

    #Initialiser les tables et les variables 
    with connection.cursor() as cursor:
        cursor.execute("""
                        INSERT INTO DMY.CET_PDF_TEMP cpt
                    SELECT 
                        rownum  AS id,
                        cc.NUM_CET ,
                        cc.SEQUENCE_NUMBER ,
                        cc.PORTFOLIO_TYPE ,
                        cc.TYPE_CONTRAT ,
                        cc.ZONE_CODE ,
                        cc.CODE_REGION ,
                        cc.UNDERWRITING_YEAR ,
                        cc.BRANCH_CODE ,
                        cc.BRANCHE ,
                        cc.SOUS_BRANCHE ,
                        cc.SUB_PROFIT_CENTRE_CODE ,
                        cc.TYPE_SOUSCRIPTION ,
                        cc.CEDANTE ,
                        nvl(cp2.PRIMES_ENCAISS,0),
                        nvl(cc2.CHARGES,0) ,
                        nvl(cc2.COURTAGE,0) ,
                        nvl(cp2.ENT_PRT_PRIME,0) ,
                        nvl(cp2.SOR_PRT_PRIME,0) ,
                        nvl(cc2.SINISTRE,0) ,
                        nvl(cp.PROV_SIN_OUV,0) ,
                        nvl(ci.PROV_SIN_CLO,0) ,
                        nvl(cp.PROV_PRI_OUV,0) ,
                        nvl(cp.PROV_PRIM_CLO,0) ,
                        nvl(cee.PROV_EGAL_OUV,0) ,
                        nvl(cee.PROV_EQUI_OUV,0) ,
                        nvl(cee.PROV_EGAL_CLO,0) ,
                        nvl(cee.PROV_EQUI_CLO,0) 
                    FROM 
                        dmy.CET_CONTRAT cc 
                        LEFT JOIN dmy.CET_CHARGES cc2 ON cc2.id = cc.ID 
                        LEFT JOIN dmy.CET_PROV cp ON cp.id = cc.id 
                        LEFT JOIN DMY.CET_PRIM cp2 ON cp2.id = cc.id 
                        LEFT JOIN dmy.CET_IBNR ci ON ci.ID = cc.id
                        LEFT JOIN DMY.CET_EGAL_EQUI cee ON cee.ID = cc.id AND (SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '2EME SEMESTRE'
                    WHERE cc.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp) AND 
                        ( nvl(cp2.PRIMES_ENCAISS,0) <>0 OR 
                            nvl(cc2.CHARGES, 0) <> 0 
                            OR nvl(cc2.COURTAGE,0) <> 0 OR 
                            nvl(cp2.ENT_PRT_PRIME,0) <> 0 OR 
                            nvl(cp2.SOR_PRT_PRIME,0) <> 0 OR 
                            nvl(cc2.SINISTRE,0) <>0 OR 
                            nvl(cp.PROV_SIN_OUV,0) <>0 OR 
                            nvl(ci.PROV_SIN_CLO,0) <>0 OR 
                            nvl(cp.PROV_PRI_OUV,0) <>0 OR 
                            nvl(cp.PROV_PRIM_CLO,0) <>0 OR 
                            nvl(cee.PROV_EGAL_OUV,0) <>0 OR 
                            nvl(cee.PROV_EGAL_CLO,0) <>0 OR 
                            nvl(cee.PROV_EQUI_OUV,0) <>0 OR 
                            nvl(cee.PROV_EQUI_CLO,0) <>0 
                            )  
                        """)
        cursor.execute("SELECT * FROM  DMY.CET_TAUX_EGAL_EQUI x WHERE x.NUM_CET =  (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)")
        les_taux = cursor.fetchone()
        taux_vie = les_taux[1]
        taux_grele = les_taux[2]
        taux_credit = les_taux[3]
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        le_cet =cursor.fetchone()
        id_cet = le_cet[0]
        cursor.callproc("DMY.CET_PROV_EGAL_EQUI",[id_cet,taux_vie,taux_grele,taux_credit])

    #Lors du 1er trimestre pour la retro, affecter aux PROV_SIN_CLO les PROV_SIN_OUV
    # pour eviter d'avoir une perte trop importante dans le net     
    #
        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)
        cursor.execute("delete from CET_PDF_FAST_V2")
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        UNDERWRITING_YEAR = row2[0]
        year = str(UNDERWRITING_YEAR)
        cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
        cursor.execute("SELECT  count(*)  FROM  (SELECT  DISTINCT spfv.TYPE_SOUSCRIPTION , SPFV .BRANCHE , SPFV .ZONE_CODE FROM DMY.CET_PDF_FAST_V2 spfv )")
        row = cursor.fetchone()
        nombre_pages = row[0]


    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y %H-%M-%S")
    name_pdf = 'CET_PROVISOIRE_'+dt_string+'.pdf'
    p = canvas.Canvas("pdf/"+name_pdf)
    

    #Creating THE PAGE DE GARDE
    p.setPageSize(portrait(A4))
    p.setFillColorRGB(84/255,119/255,157/255)

    # THE RECTANGLE AT THE TOP OF THE PAGE
    p.rect(0,712,600,130, fill=1 ,stroke=False) 

    # THE RECTANGLE AT THE MIDDLE OF THE PAGE
    p.setFillColorRGB(156/255,158/255,159/255)
    p.rect(0,132,600,580, fill=1 ,stroke=False)
    
    #THE TEXTE AT THE TOP OF THE PAGE 
    p.setFillColorRGB(255/255,255/255,255/255)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30, 790, "COMPTE D'EXPLOITATION TECHNIQUE")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(30, 770, "COMPAGNIE CENTRALE DE REASSURANCE" )
    p.drawString(30, 750, str(exercice) )
    #THE IMAGE AT AND THE SLOGAN AT THE BOTTOM OF THE PAGE 
    Image =ImageReader('img/logoShort.png')
    p.drawImage(Image,420,30, width=114,height=70,mask='auto')
    p.setFillColorRGB(84/255,119/255,157/255)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, 50, "Serving your challenges, Supporting your activity" )

    #THE YEAR AT THE MIDDLE OF THE PAGE
    p.setFont("Helvetica", 210)
    p.drawString(90, 180, str(UNDERWRITING_YEAR)  )

    p.showPage()
    #THE SOMMAIRE 
    p.setFont("Helvetica", 25)
    p.setFillColorRGB(84/255,119/255,157/255)

    page_sommaire = 1 
    
    souscription = ' '
    for k1 in type_souscriptions :
        x=158
        y=700
        
        p.setFillColorRGB(84/255,119/255,157/255)
        p.setFont("Helvetica", 15)
        p.drawString(45, 770, "SOMMAIRE       "+str(exercice)+" "+str(UNDERWRITING_YEAR) )
        p.setFont("Helvetica", 10)
        p.drawString(x, y+30, decoderSouscriton(k1))
        y =y -20
        branches_deja_fait =[]
        for j1 in branches :
            for i1 in zones :
                condition1 = True
                condition2 = True
                p.setFillColorRGB(0/255,0/255,0/255)
                page = Pdf_fast_v2.objects.filter(type_souscription= k1).filter(branche=j1).filter(zone_code = i1)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :     
                    condition2= False
                if (condition1 == True) or (condition2 == True) : 
                    if k1 == 'A' and j1 not in branches_deja_fait :
                        branches_deja_fait.append(j1)
                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), 
                                                 ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                        
                        
                    elif k1 =='R' or k1 =='N' :

                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data ,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                    page_sommaire = page_sommaire + 1 
        p.showPage()       

    #PRINT THE TABLES 
    p.setPageSize(landscape(A4))

    
    
    
    #Condition to check if a page is empty
    condition1 = True
    condition2 = True
    #table_pdf = Pdf_fast_v2.objects.all()
    page_en_cours = 1

    for k in type_souscriptions :
        for j in branches :
            for i in zones :

                #Condition to check if a page is empty
                condition1 = True
                condition2 = True

                page = Pdf_fast_v2.objects.filter(type_souscription= k).filter(branche=j).filter(zone_code = i)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    p1= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :
                    p2= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)     
                    condition2= False 
                

            # check if page is empty
                if (condition1 == True) or (condition2 == True) : 

            #Formating data with thousands separator and eliminate the 0.00 and replace it with empty String
                    ligne1 = [   p1.sinistre_1 , p2.sinistre_1 , (p1.sinistre_1 + p2.sinistre_1) ]
                    ligne1formated = ['SINISTRES REGLES ET RACHAT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne1]
                    ligne2 = [  p1.prov_sin_ouv_2,  p2.prov_sin_ouv_2, (p1.prov_sin_ouv_2+ p2.prov_sin_ouv_2) ]
                    ligne2formated = ['PROVISION SINISTRE OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne2]
                    ligne3 = [   p1.prov_sin_clo_3,  p2.prov_sin_clo_3 ,(p1.prov_sin_clo_3+ p2.prov_sin_clo_3) ]
                    ligne3formated = ['PROVISION SINISTRE CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne3]
                    ligne4 = [  p1.SINISTRES_COMP_EXE_4,  p2.SINISTRES_COMP_EXE_4 ,(p1.SINISTRES_COMP_EXE_4 +p2.SINISTRES_COMP_EXE_4)]
                    ligne4formated = ['SINISTRES DE COMPETENCE EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne4]
                    ligne6 =  [   p1.les_charges_6 ,  p2.les_charges_6 ,(p1.les_charges_6+p2.les_charges_6)]
                    ligne6formated = ['COMMISSIONS ET CHARGES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne6]
                    ligne8 = [   p1.courtage_8,  p2.courtage_8,(p1.courtage_8+p2.courtage_8)]
                    ligne8formated = ['COURTAGE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if '{:,.2f}'.format(elem) != '0.00' else '' for elem in ligne8]
                    ligne9 = [   p1.prov_egal_ouv_24,  p2.prov_egal_ouv_24, (p1.prov_egal_ouv_24+ p2.prov_egal_ouv_24)]
                    ligne9formated = ['PROVISIONS EGALISATION OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne9]
                    ligne10 = [   p1.prov_equi_ouv_25 ,  p2.prov_equi_ouv_25, (p1.prov_equi_ouv_25+ p2.prov_equi_ouv_25) ]
                    ligne10formated = ['PROVISIONS EQUILIBRAGE OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00'  else '' for elem in ligne10]
                    ligne11 = [  p1.prov_egal_clo_26 ,  p2.prov_egal_clo_26,(p1.prov_egal_clo_26 +p2.prov_egal_clo_26) ]
                    ligne11formated = ['PROVISIONS EGALISATION CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne11]
                    ligne12 =[  p1.prov_equi_clo_27,  p2.prov_equi_clo_27,(p1.prov_equi_clo_27+p2.prov_equi_clo_27)]
                    ligne12formated = ['PROVISIONS EQUILIBRAGE CLOTURE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne12]
                    ligne13 = [  p1.prov_egal_clo_ouv_22 ,  p2.prov_egal_clo_ouv_22,(p1.prov_egal_clo_ouv_22+p2.prov_egal_clo_ouv_22)]
                    ligne13formated = ['PROVISIONS EGALISATION CLOTURE-OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne13]
                    ligne14 = [   p1.prov_equi_clo_ouv_23 ,  p2.prov_equi_clo_ouv_23, (p1.prov_equi_clo_ouv_23+p2.prov_equi_clo_ouv_23)]
                    ligne14formated = ['PROVISIONS EQUILIBRAGE CLOTURE-OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne14]
                    ligne15 = [   p1.total_9 ,  p2.total_9 ,(p1.total_9+p2.total_9)]
                    ligne15formated = ['TOTAL']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne15]
                    ligne16 = [  p1.primes_encaiss_10 ,  p2.primes_encaiss_10,(p1.primes_encaiss_10+p2.primes_encaiss_10)]
                    ligne16formated = ['PRIMES EMISES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne16]
                    ligne17 = [  p1.ent_prt_prime_11, p2.ent_prt_prime_11,(p1.ent_prt_prime_11 + p2.ent_prt_prime_11)]
                    ligne17formated = ['ENTREES PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne17]
                    ligne18 = [  p1.sor_prt_prime_12,  p2.sor_prt_prime_12,(p1.sor_prt_prime_12+p2.sor_prt_prime_12)]
                    ligne18formated = ['SORTIE PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne18]
                    ligne19 = [  p1.primes_nettes_13 ,  p2.primes_nettes_13,(p1.primes_nettes_13+p2.primes_nettes_13)]
                    ligne19formated = ['PRIMES NETTES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne19]
                    ligne20 = [  p1.primes_nettes_ann_16 ,   p2.primes_nettes_ann_16 ,(p1.primes_nettes_ann_16+p2.primes_nettes_ann_16)]
                    ligne20formated = ['PRIMES NETTES ANNUELLES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne20]
                    ligne21 = [  p1.prov_pri_ouv_17,   p2.prov_pri_ouv_17,(p1.prov_pri_ouv_17+p2.prov_pri_ouv_17)]
                    ligne21formated = ['PROVISION PRIME OUVERTURE']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne21]
                    ligne22 = [  p1.prov_prim_clo_18,  p2.prov_prim_clo_18,(p1.prov_prim_clo_18+p2.prov_prim_clo_18)]
                    ligne22formated = ['PROVISION PRIME CLOTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne22]
                    ligne23 = [  p1.primes_acquises_exe_19 ,  p2.primes_acquises_exe_19,(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19)]
                    ligne23formated = ['PRIMES ACQUISES EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne23]
                    ligne24 = [  p1.BENEFICE_PERTE_20 ,  p2.BENEFICE_PERTE_20,(p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)]
                    ligne24formated = ['BENEFICE/PERTE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne24]
                    

        # Format data to eliminate the 0.00 and the -0.00 and replace it with empty String
                    ligne1SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne1formated]
                    ligne2SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne2formated]
                    ligne3SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne3formated]
                    ligne4SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne4formated]
                    ligne6SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne6formated]
                    ligne8SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne8formated]
                    ligne9SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne9formated]
                    ligne10SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne10formated]
                    ligne11SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne11formated]
                    ligne12SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne12formated]
                    ligne13SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne13formated]
                    ligne14SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne14formated]
                    ligne15SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne15formated]
                    ligne16SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne16formated]
                    ligne17SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne17formated]
                    ligne18SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne18formated]
                    ligne19SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne19formated]
                    ligne20SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne20formated]
                    ligne21SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne21formated]
                    ligne22SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne22formated]
                    ligne23SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne23formated]
                    ligne24SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne24formated]


        #Reset values of totals
                    total_5 = 0
                    total_21 = 0
                    total_7 = 0
        # SPECIAL CALCULS WHITH DIVISIONS THE 5 7 AND 21 
                    if ((p1.primes_encaiss_10+p2.primes_encaiss_10) !=0 ) : 
                        total_7 = abs (100*(p1.les_charges_6+p2.les_charges_6)/(p1.primes_encaiss_10+p2.primes_encaiss_10))
                    if ( (p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) !=0 ) :
                        total_21 = abs ( 100*( (p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)/(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) ) )
                    if ( ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) ) != 0  ) :
                        total_5 = abs ( 100*( (p1.sinistre_1+p2.sinistre_1) -(p1.prov_sin_ouv_2+p2.prov_sin_ouv_2)+(p1.prov_sin_clo_3+p2.prov_sin_clo_3) )/ ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) )    )
        # Formating the special lines            
                    
                    ligne5  =  [p1.SINISTRES_PRIMES_ACQU_5 ,  p2.SINISTRES_PRIMES_ACQU_5 ,total_5]
                    ligne5formated = ['SINISTRES/PRIMES ACQUISES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne5]  
                    ligne5SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne5formated]
                    
                    ligne7 = [  p1.commissions_primes_7,  p2.commissions_primes_7,total_7]
                    ligne7formated = ['COMMISSIONS/PRIMES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne7]
                    ligne7SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne7formated]

                    ligne25 = [  p1.rn_pra_21,  p2.rn_pra_21,total_21]
                    ligne25formated = ['RN/PRA  %']+[ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne25]
                    ligne25SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne25formated]

                    data = [
                        ['BRANCHE '+decoderBranche(j), 'TRAITES', 'FACULTATIVES', 'TOTAL'],
                        ligne1SuperFormated,
                        ligne2SuperFormated,
                        ligne3SuperFormated,
                        ligne4SuperFormated,
                        ligne5SuperFormated,
                        ligne6SuperFormated,
                        ligne7SuperFormated,
                        ligne8SuperFormated,
                        ligne9SuperFormated,
                        ligne10SuperFormated,
                        ligne11SuperFormated,
                        ligne12SuperFormated,        
                        ligne13SuperFormated,
                        ligne14SuperFormated,
                        ligne15SuperFormated,
                        ligne16SuperFormated,
                        ligne17SuperFormated,        
                        ligne18SuperFormated,
                        ligne19SuperFormated,
                        ligne20SuperFormated,
                        ligne21SuperFormated,
                        ligne22SuperFormated,
                        ligne23SuperFormated,
                        ligne24SuperFormated,
                        ligne25SuperFormated]
                        
                    width = 400
                    height = 100
                    
        #DEFINE THE STYLING OF THE DATA TABLE

                    p.setFont('Times-Roman', 10)
                    f = Table(data ,colWidths=[252,140,140,140], 
                                    rowHeights=[18,25,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15])
                    f.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                        ('ALIGN', (0,0), (0,25), 'LEFT'),
                        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                        ('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,0), (-1,0), 1.4, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,1), (-1,24), 0.7, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,25), (-1,25), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('VALIGN',(0,0),(3,0),'MIDDLE'),
                        ('VALIGN',(0,2),(-1,-1),'MIDDLE'),
                        ('BACKGROUND',(3,0),(3,25),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('BACKGROUND',(0,15),(3,15),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('TEXTCOLOR',(0,0),(3,0),colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('TEXTCOLOR',(0,1),(-1,-1),colors.Color(red=(0/255),green=(0/255),blue=(0/255))),
                        ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                        ('FONTSIZE', (1,1), (-1, -1), 10), 
                        ]))
                    f.wrapOn(p, width, height)
                    f.drawOn(p,76, 40) 

        #PRINT THE SOUSCRIPTION AND ZONE
                    p.setFont("Helvetica-Bold", 13)
                    p.setFillColorRGB(84/255,119/255,157/255) #choose your font colour
                    zone_texte = ''
                    if k == 'A' : 
                        zone_texte = decoderZone(i)
                    
                    p.drawString(82, 480, decoderSouscriton(k)+' '+ zone_texte)

                #PRINT THE OTHER LINES 
                    p.setFont("Helvetica-Bold", 17)
                    p.drawString(82, 550, "COMPTE D'EXPLOITATION TECHNIQUE" )
                    p.setFont("Helvetica", 11)
                    p.drawString(82, 530, "PAR BRANCHES ET REGIONS EN DINARS ALGERIENS" )
                    p.setFont("Helvetica", 9)

                #PRINT THE IMAGE LOGO and OTHER STUFF
                    p.setFillColorRGB(0/255,0/255,0/255)
                    #p.drawString(82, 450, "EN MILLION DE DINARS")
                    p.drawString(688, 450, "ANNEE "+year)
                    Image =ImageReader('img/logo02.png')
                    p.drawImage(Image,452,525, width=297,height=52,mask='auto')   

                # PRINT THE PAGE NUMBER AND THE DATE
                    p.drawString(688, 23,"PAGE "+str(page_en_cours)+"/"+str(nombre_pages))
                    today = date.today()
                    d1 = today.strftime("%d/%m/%Y %H-%M-%S")
                    p.drawString(82, 23,dt_string.replace('_','/'))
                    page_en_cours = page_en_cours+1

                #GO TO THE NEXT PAGE

                    p.showPage()
    # Close the PDF object cleanly, and we're done.

    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.

    buffer.seek(0)
    # GET THE STATUS OF RMS SYSTEM
    with connection.cursor() as cursor:
        cursor.execute(" SELECT scp.IS_RMS_ACTIVE FROM dmy.CET_PARAMETRES scp ")
        row5 = cursor.fetchone()
        rms_active = row5[0]

    context = {
        'name_pdf': name_pdf ,
        'rms_active' : rms_active ,
        'origine' : 'prov_egal_equi'
    }
    #return FileResponse(buffer, as_attachment=True, filename='hello.pdf')
    
    return render(request, 'main/templates/pdf.html' , context )

@login_required
@permission_required('cet.view_prov_egal_equi' ,raise_exception =True)
def valider_prov_egal_equi(request) :
    #Retrieve data 
    name_pdf = 'teste.pdf'
    if request.method == 'POST':
        name_pdf = request.POST.get('name_pdf')
    error = -1 
    #Initialiser les tables et les variables 
    with connection.cursor() as cursor:
        cursor.execute("""
                        INSERT INTO DMY.CET_PDF_TEMP cpt
                    SELECT 
                        rownum  AS id,
                        cc.NUM_CET ,
                        cc.SEQUENCE_NUMBER ,
                        cc.PORTFOLIO_TYPE ,
                        cc.TYPE_CONTRAT ,
                        cc.ZONE_CODE ,
                        cc.CODE_REGION ,
                        cc.UNDERWRITING_YEAR ,
                        cc.BRANCH_CODE ,
                        cc.BRANCHE ,
                        cc.SOUS_BRANCHE ,
                        cc.SUB_PROFIT_CENTRE_CODE ,
                        cc.TYPE_SOUSCRIPTION ,
                        cc.CEDANTE ,
                        nvl(cp2.PRIMES_ENCAISS,0),
                        nvl(cc2.CHARGES,0) ,
                        nvl(cc2.COURTAGE,0) ,
                        nvl(cp2.ENT_PRT_PRIME,0) ,
                        nvl(cp2.SOR_PRT_PRIME,0) ,
                        nvl(cc2.SINISTRE,0) ,
                        nvl(cp.PROV_SIN_OUV,0) ,
                        nvl(ci.PROV_SIN_CLO,0) ,-----MODIF ICI
                        nvl(cp.PROV_PRI_OUV,0) ,
                        nvl(cp.PROV_PRIM_CLO,0) ,
                        nvl(cee.PROV_EGAL_OUV,0) ,
                        nvl(cee.PROV_EQUI_OUV,0) ,
                        nvl(cee.PROV_EGAL_CLO,0) ,
                        nvl(cee.PROV_EQUI_CLO,0) 
                    FROM 
                        dmy.CET_CONTRAT cc 
                        LEFT JOIN dmy.CET_CHARGES cc2 ON cc2.id = cc.ID 
                        LEFT JOIN dmy.CET_PROV cp ON cp.id = cc.id 
                        LEFT JOIN DMY.CET_PRIM cp2 ON cp2.id = cc.id 
                        LEFT JOIN dmy.CET_IBNR ci ON ci.ID = cc.id
                        LEFT JOIN DMY.CET_EGAL_EQUI cee ON cee.ID = cc.id AND (SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '2EME SEMESTRE'
                    WHERE cc.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp) AND 
                        ( nvl(cp2.PRIMES_ENCAISS,0) <>0 OR 
                            nvl(cc2.CHARGES, 0) <> 0 
                            OR nvl(cc2.COURTAGE,0) <> 0 OR 
                            nvl(cp2.ENT_PRT_PRIME,0) <> 0 OR 
                            nvl(cp2.SOR_PRT_PRIME,0) <> 0 OR 
                            nvl(cc2.SINISTRE,0) <>0 OR 
                            nvl(cp.PROV_SIN_OUV,0) <>0 OR 
                            nvl(ci.PROV_SIN_CLO,0) <>0 OR 
                            nvl(cp.PROV_PRI_OUV,0) <>0 OR 
                            nvl(cp.PROV_PRIM_CLO,0) <>0 OR 
                            nvl(cee.PROV_EGAL_OUV,0) <>0 OR 
                            nvl(cee.PROV_EGAL_CLO,0) <>0 OR 
                            nvl(cee.PROV_EQUI_OUV,0) <>0 OR 
                            nvl(cee.PROV_EQUI_CLO,0) <>0 
                            )  
                        """)
        cursor.execute("SELECT * FROM  DMY.CET_TAUX_EGAL_EQUI x WHERE x.NUM_CET =  (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)")
        les_taux = cursor.fetchone()
        taux_vie = les_taux[1]
        taux_grele = les_taux[2]
        taux_credit = les_taux[3]
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        le_cet =cursor.fetchone()
        id_cet = le_cet[0]
        cursor.callproc("DMY.CET_PROV_EGAL_EQUI",[id_cet,taux_vie,taux_grele,taux_credit])# APPLIQUER LES TAUX
        cursor.callproc("INSERER_EGAL_EQUI")# INSERER DANS LES TABLES DE BASES
        
    context = {
        'validation_egal_equi': 1 ,
        'message'  : 'Validation des PROV. EGAL-EQUI réussie' ,
        'name_pdf': name_pdf
    }
   
    return render(request, 'main/templates/pdf.html',context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.management' ,raise_exception =True)
def management(request) :
    liste_user= []
    with connection.cursor() as cursor :
        cursor.execute("SELECT scp.IS_RMS_ACTIVE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        cursor.execute("""
                     SELECT 	 x.USER_ID 
                            ,ud.USERNAME 
                            ,x.ROLE_ID 
                            ,ag.NAME AS DEPARTMENT 
                    FROM RMS_TABLES.USER_MASTER x
                    JOIN RMS_TABLES.USER_DETAIL ud ON ud.USER_ID =x.USER_ID
                    LEFT JOIN DMY.AUTH_USER au ON au.FIRST_NAME = ud.USERNAME
                    LEFT JOIN DMY.AUTH_USER_GROUPS aug ON aug.USER_ID = au.ID 
                    LEFT JOIN dmy.AUTH_GROUP ag ON ag.ID = aug.GROUP_ID 
                    WHERE x.ACCESS_LEVEL != -1
                    AND   x.USER_ID   NOT IN ('DMY')
                    AND   ( ag.NAME IN ('DFC','DT','DSI' ,'DRDAP', 'DG', 'DRIE', 'DAI', 'DFC' ) )
                    AND   (au.IS_ACTIVE = 1 OR au.IS_ACTIVE IS NULL )
                    ORDER BY ag.NAME , ud.USERNAME 
                    """)
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_user.append(liste1)
    
    if (data == 1) :
        message = "Le système RMS est actif."
    if (data == 0) :
        message = "Le système RMS est bloqué."
    context = {
        'message' : message ,
        'active' : data ,
        'liste_user' : liste_user ,
    }
    return render(request, 'main/templates/management.html' , context)

@login_required
@permission_required('cet.management' ,raise_exception =True)
def bloquer_rms(request) :
    liste_user= []
    with connection.cursor() as cursor:
        
        #KILL ALL THE SESSIONS
        cursor.execute(""" 
                        BEGIN
                            FOR r IN (select sid,serial# from v$session where username NOT in ('DOP','SYS','DMY') )
                            LOOP
                                EXECUTE IMMEDIATE 'alter system kill session ''' || r.sid 
                                || ',' || r.serial# || '''';
                            END LOOP;
                        END;
                        """)
        cursor.execute("DELETE FROM DMY.USER_BACKUP x")
        cursor.execute("INSERT INTO DMY.USER_BACKUP x SELECT x.*,sysdate AS backup_date FROM RMS_TABLES.USER_MASTER x")
        cursor.execute("UPDATE  RMS_TABLES.USER_MASTER x SET x.ROLE_ID = 'ENQUIRY'" )
        cursor.execute("UPDATE dmy.CET_PARAMETRES scp SET scp.IS_RMS_ACTIVE = 0")
        cursor.execute("SELECT scp.IS_RMS_ACTIVE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        cursor.execute("""
                     SELECT 	 x.USER_ID 
                            ,ud.USERNAME 
                            ,x.ROLE_ID 
                            ,ag.NAME AS DEPARTMENT 
                    FROM RMS_TABLES.USER_MASTER x
                    JOIN RMS_TABLES.USER_DETAIL ud ON ud.USER_ID =x.USER_ID
                    LEFT JOIN DMY.AUTH_USER au ON au.FIRST_NAME = ud.USERNAME
                    LEFT JOIN DMY.AUTH_USER_GROUPS aug ON aug.USER_ID = au.ID 
                    LEFT JOIN dmy.AUTH_GROUP ag ON ag.ID = aug.GROUP_ID 
                    WHERE x.ACCESS_LEVEL != -1
                    AND   ( ag.NAME IN ('DFC','DT','DSI' ,'DRDAP', 'DG', 'DRIE', 'DAI', 'DFC' ) )
                    AND   (au.IS_ACTIVE = 1 OR au.IS_ACTIVE IS NULL )
                    ORDER BY ag.NAME , ud.USERNAME 
                    """)
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_user.append(liste1)
    context = {
        'message' : 'Le système RMS est bloqué.' ,
        'active' : data ,
        'liste_user' : liste_user ,
    }
    return render(request, 'main/templates/management.html' , context)

@login_required
@permission_required('cet.management' ,raise_exception =True)
def debloquer_rms(request) :
    liste_user= []
    with connection.cursor() as cursor:
        cursor.execute("UPDATE dmy.CET_PARAMETRES scp SET scp.IS_RMS_ACTIVE = 1")
        cursor.execute("SELECT scp.IS_RMS_ACTIVE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        cursor.execute(""" 
                        UPDATE RMS_TABLES.USER_MASTER a
                        SET a.ROLE_ID = (SELECT x.ROLE_ID
                                        FROM DMY.USER_BACKUP x
                                        WHERE x.USER_ID = a.USER_ID)
                        WHERE EXISTS (
                            SELECT 1
                            FROM DMY.USER_BACKUP x
                            WHERE x.USER_ID = a.USER_ID
                        ) 
                        """)
        cursor.execute("""
                     SELECT 	 x.USER_ID 
                            ,ud.USERNAME 
                            ,x.ROLE_ID 
                            ,ag.NAME AS DEPARTMENT 
                    FROM RMS_TABLES.USER_MASTER x
                    JOIN RMS_TABLES.USER_DETAIL ud ON ud.USER_ID =x.USER_ID
                    LEFT JOIN DMY.AUTH_USER au ON au.FIRST_NAME = ud.USERNAME
                    LEFT JOIN DMY.AUTH_USER_GROUPS aug ON aug.USER_ID = au.ID 
                    LEFT JOIN dmy.AUTH_GROUP ag ON ag.ID = aug.GROUP_ID 
                    WHERE x.ACCESS_LEVEL != -1
                    AND   ( ag.NAME IN ('DFC','DT','DSI' ,'DRDAP', 'DG', 'DRIE', 'DAI', 'DFC' ) )
                    AND   (au.IS_ACTIVE = 1 OR au.IS_ACTIVE IS NULL )
                    ORDER BY ag.NAME , ud.USERNAME 
                    """)
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_user.append(liste1)
    context = {
        'message' : 'Le système RMS est actif.' ,
        'active' : data ,
        #'liste_user' : liste_user ,
    }
    return render(request, 'main/templates/management.html' , context)

@login_required
@permission_required('cet.management' ,raise_exception =True)
def bloquer_user(request) :
    liste_user= []
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.IS_RMS_ACTIVE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        #KILL THE SESSION OF THE USER
        cursor.execute("""
                        BEGIN
                            FOR r IN (select sid,serial# from v$session where username  in (%s) )
                            LOOP
                                EXECUTE IMMEDIATE 'alter system kill session ''' || r.sid 
                                || ',' || r.serial# || '''';
                            END LOOP;
                        END;
                    """,[user_id])
        #CHANGE THE ROLE_ID
        cursor.execute("UPDATE  RMS_TABLES.USER_MASTER x SET x.ROLE_ID = 'ENQUIRY' WHERE x.USER_ID = %s",[user_id])
        cursor.execute("""
                     SELECT 	 x.USER_ID 
                            ,ud.USERNAME 
                            ,x.ROLE_ID 
                            ,ag.NAME AS DEPARTMENT 
                    FROM RMS_TABLES.USER_MASTER x
                    JOIN RMS_TABLES.USER_DETAIL ud ON ud.USER_ID =x.USER_ID
                    LEFT JOIN DMY.AUTH_USER au ON au.FIRST_NAME = ud.USERNAME
                    LEFT JOIN DMY.AUTH_USER_GROUPS aug ON aug.USER_ID = au.ID 
                    LEFT JOIN dmy.AUTH_GROUP ag ON ag.ID = aug.GROUP_ID 
                    WHERE x.ACCESS_LEVEL != -1
                    AND   ( ag.NAME IN ('DFC','DT','DSI' ,'DRDAP', 'DG', 'DRIE', 'DAI', 'DFC' ) )
                    AND   (au.IS_ACTIVE = 1 OR au.IS_ACTIVE IS NULL )
                    ORDER BY ag.NAME , ud.USERNAME 
                    """)
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_user.append(liste1)
    context = {
        'message' : 'Le système RMS est bloqué.' ,
        'active' : data ,
        'liste_user' : liste_user ,
    }
    return render(request, 'main/templates/management.html' , context)  

@login_required
@permission_required('cet.management' ,raise_exception =True)
def debloquer_user(request) :
    liste_user= []
    if request.method == 'GET':
        user_id = request.GET.get('user_id')
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.IS_RMS_ACTIVE FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        data =row[0]
        #RESTTORE THE PERVIOUS ROLE_ID
        cursor.execute("""
                        UPDATE RMS_TABLES.USER_MASTER a
                        SET a.ROLE_ID = (SELECT x.ROLE_ID
                                        FROM DMY.USER_BACKUP x
                                        WHERE x.USER_ID = a.USER_ID
                                        AND x.USER_ID = %s)
                        WHERE EXISTS (
                            SELECT 1
                            FROM DMY.USER_BACKUP x
                            WHERE x.USER_ID = a.USER_ID
                            AND x.USER_ID = %s) 
                            """,[user_id,user_id])
        cursor.execute("""
                     SELECT 	 x.USER_ID 
                            ,ud.USERNAME 
                            ,x.ROLE_ID 
                            ,ag.NAME AS DEPARTMENT 
                    FROM RMS_TABLES.USER_MASTER x
                    JOIN RMS_TABLES.USER_DETAIL ud ON ud.USER_ID =x.USER_ID
                    LEFT JOIN DMY.AUTH_USER au ON au.FIRST_NAME = ud.USERNAME
                    LEFT JOIN DMY.AUTH_USER_GROUPS aug ON aug.USER_ID = au.ID 
                    LEFT JOIN dmy.AUTH_GROUP ag ON ag.ID = aug.GROUP_ID 
                    WHERE x.ACCESS_LEVEL != -1
                    AND   ( ag.NAME IN ('DFC','DT','DSI' ,'DRDAP', 'DG', 'DRIE', 'DAI', 'DFC' ) )
                    AND   (au.IS_ACTIVE = 1 OR au.IS_ACTIVE IS NULL )
                    ORDER BY ag.NAME , ud.USERNAME 
                    """)
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_user.append(liste1)
    context = {
        'message' : 'Le système RMS est bloqué.' ,
        'active' : data ,
        'liste_user' : liste_user ,
    }
    return render(request, 'main/templates/management.html' , context)

@login_required
@permission_required('cet.super_management' ,raise_exception =True)
def super_management(request) :
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        DATE_DEBUT_EXERCICE =row[1]
        DATE_REC =row[2]
        EXERCICE =row[3]
        CET_OUVERTURE =row[4]
        UNDERWRITING_YEAR =row[5]
        CET_ENCOURS =row[6]
        IS_RMS_ACTIVE =row[7]
    context = {
        'DATE_DEBUT_EXERCICE' : DATE_DEBUT_EXERCICE ,
        'DATE_REC' : DATE_REC ,
        'EXERCICE' : EXERCICE ,
        'CET_OUVERTURE' : CET_OUVERTURE ,
        'UNDERWRITING_YEAR' : UNDERWRITING_YEAR ,
        'CET_ENCOURS' : CET_ENCOURS ,
        'IS_RMS_ACTIVE' : IS_RMS_ACTIVE,
    }
    return render(request, 'main/templates/super_management.html' , context)

@login_required
@permission_required('cet.super_management' ,raise_exception =True)
def cet_suivant(request) :
    #GET THE DATA IN TABLE STORE_CET_PARAMETRE
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.EXERCICE FROM dmy.CET_PARAMETRES scp ")
        row = cursor.fetchone()
        old_exercice = row[0]

        cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM dmy.CET_PARAMETRES scp ")
        row1 = cursor.fetchone()
        old_underwriting_year = row1[0]

    #GET THE NEW EXERCICE 
    if old_exercice == '1ER TRIMESTRE' : 
        new_exercice = '1ER SEMESTRE'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.EXERCICE = %s ",[new_exercice])
    if old_exercice == '1ER SEMESTRE' : 
        new_exercice = '3EME TRIMESTRE'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.EXERCICE = %s ",[new_exercice])
    if old_exercice == '3EME TRIMESTRE' : 
        new_exercice = '2EME SEMESTRE'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.EXERCICE = %s ",[new_exercice])
    if old_exercice == '2EME SEMESTRE' : 
        new_exercice = '1ER TRIMESTRE'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.EXERCICE = %s ",[new_exercice])

    #update the DATE_DEBUT_EXERCICE
    if old_exercice == '2EME SEMESTRE' : 
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.DATE_DEBUT_EXERCICE = sysdate ")

    #UPDATE THE DATE_REC
    if new_exercice == '1ER TRIMESTRE' :
        new_date_rec = str(old_underwriting_year)+'/03/31'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.DATE_REC = TO_DATE('"+ new_date_rec +"','yyyy/mm/dd') ")
    if new_exercice == '1ER SEMESTRE' :
        new_date_rec = str(old_underwriting_year)+'/06/30'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.DATE_REC = TO_DATE('"+ new_date_rec +"','yyyy/mm/dd') ")
    if new_exercice == '3EME TRIMESTRE' :
        new_date_rec = str(old_underwriting_year)+'/09/30'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.DATE_REC = TO_DATE('"+ new_date_rec +"','yyyy/mm/dd') ")
    if new_exercice == '2EME SEMESTRE' :
        new_date_rec = str(old_underwriting_year)+'/12/31'
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.DATE_REC = TO_DATE('"+ new_date_rec +"','yyyy/mm/dd') ")
    
    #UPDATE CET OUVERTURE AND UNDERWRITING_YEAR
    if old_exercice == '2EME SEMESTRE' : 
        with connection.cursor() as cursor:
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.CET_REOUVERTURE = (SELECT MAX(cp.NUM_CET) FROM dmy.CET_PERIODE cp WHERE cp.PERIODE ='2EME SEMESTRE')")
            cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.UNDERWRITING_YEAR =  scp.UNDERWRITING_YEAR + 1")
    
    #UPDATE THE CET_EN_COURS
    with connection.cursor() as cursor:
        cursor.execute("UPDATE dmy.CET_PARAMETRES scp  SET scp.CET_EN_COURS = CET_EN_COURS + 5")

    #GET THE DATA FOR THE DISPLAY
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM DMY.CET_PARAMETRES scp")
        row = cursor.fetchone()
        DATE_DEBUT_EXERCICE =row[1]
        DATE_REC =row[2]
        EXERCICE =row[3]
        CET_OUVERTURE =row[4]
        UNDERWRITING_YEAR =row[5]
        CET_ENCOURS =row[6]
        IS_RMS_ACTIVE =row[7]
    context = {
        'DATE_DEBUT_EXERCICE' : DATE_DEBUT_EXERCICE ,
        'DATE_REC' : DATE_REC ,
        'EXERCICE' : EXERCICE ,
        'CET_OUVERTURE' : CET_OUVERTURE ,
        'UNDERWRITING_YEAR' : UNDERWRITING_YEAR ,
        'CET_ENCOURS' : CET_ENCOURS ,
        'IS_RMS_ACTIVE' : IS_RMS_ACTIVE,
    }
    return render(request, 'main/templates/super_management.html' , context)
    
@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def top_list(request) :
    liste_top_prime = []
    liste_top_sinistre= []
    liste_top_engagement_acc= []
    liste_top_engagement_retro= []
    with connection.cursor() as cursor :
    #TOP PRIME
        cursor.execute("SELECT  tp.* FROM DMY.TOP_PRIME_M tp ")
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 2 :
                    cell_data = round(cell_data,0)
                liste1.append(str(cell_data))
            liste_top_prime.append(liste1)
    #TOP SINISTRE
        cursor.execute("SELECT  tp.* FROM DMY.TOP_sinistre_M tp ")
        page2 = cursor.fetchall()
        for row_num, columns in enumerate(page2):
            liste2 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 2 :
                    cell_data = round(cell_data,0)
                liste2.append(str(cell_data))
            liste_top_sinistre.append(liste2)
    # TOP_ENGAGEMENT_ACC
        cursor.execute("SELECT  tp.* FROM DMY.TOP_ENGAGEMENT_ACC_M tp ")
        page3 = cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste3 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 2 :
                    cell_data = round(cell_data,0)
                liste3.append(str(cell_data))
            liste_top_engagement_acc.append(liste3)
    # TOP_ENGAGEMENT_RETROCESSION
        cursor.execute("SELECT  tp.* FROM DMY.TOP_ENGAGEMENT_RETRO_M tp ")
        page4 = cursor.fetchall()
        for row_num, columns in enumerate(page4):
            liste4 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 2 :
                    cell_data = round(cell_data,0)
                liste4.append(str(cell_data))
            liste_top_engagement_retro.append(liste4)
    dataDictionary = {
        'liste_top_prime' : liste_top_prime ,
        'liste_top_sinistre' : liste_top_sinistre ,
        'liste_top_engagement_acc' : liste_top_engagement_acc ,
        'liste_top_engagement_retro' : liste_top_engagement_retro ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    context = {
        'data' : dataJSON ,
    }
    return render (request , 'main/templates/top_list.html',context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def kri_view(request) :
    part_prime_courtier = 0 
    part_prime_courtier_retro = 0 
    liste_loss_ratio = []
    liste_engagement_securite = []
    liste_risque_defaut = []
    with connection.cursor() as cursor :

        #INITIALIZE AND INSERT INTO DMY.STORE_PDF_FAST_V2
        cursor.execute("INSERT INTO DMY.CET_PDF_TEMP cpt SELECT rownum  AS id ,cm2.* FROM DMY.CET_M cm2 ")
        #Lors du 1er trimestre pour la retro, affecter aux PROV_SIN_CLO les PROV_SIN_OUV
        # pour eviter d'avoir une perte trop importante dans le net     
        #
        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)
        cursor.execute("delete from  DMY.CET_PDF_FAST_V2")
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
        #END OF THE INITIALIZATION

        cursor.execute("SELECT * FROM DMY.KRI_PART_PRIME_COURTIER_M kppc") 
        row1 = cursor.fetchone()
        part_prime_courtier = str(row1[0])
        cursor.execute("SELECT * FROM DMY.KRI_PART_PRIME_COURTIER_RET_M kppcr") 
        row2 = cursor.fetchone()
        part_prime_courtier_retro = str(row2[0])
        #LOSS RATIO
        cursor.execute("SELECT klr.*,klr.LOSS_RATIO FROM DMY.KRI_LOSS_RATIO_M klr ORDER BY klr.BRANCHE ,KLR.ZONE_CODE , klr.TYPE_SOUSCRIPTION")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 4 :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                liste1.append(str(cell_data))
            liste_loss_ratio.append(liste1)
    #TABLEAU ENGAGEMENT SECURITE
        cursor.execute("SELECT rownum AS id , kpes.* FROM DMY.KRI_PART_ENGAGEMENT_SECU_M kpes ORDER BY  kpes.ENGAGEMENTS DESC   ")
        page2 = cursor.fetchall()
        for row_num, columns in enumerate(page2):
            liste2 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 3 :
                    cell_data =round(cell_data,0)
                liste2.append(str(cell_data))
            liste_engagement_securite.append(liste2)

    #TABLEAU RISQUE DEFAUT
        cursor.execute(" SELECT rownum AS id ,tt.* FROM (SELECT krd.* FROM DMY.KRI_RISQUE_DEFAUT_M krd ORDER BY krd.RISQUE_DEFAUT DESC)tt ")
        page3 = cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste3 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 3 :
                    cell_data =round(cell_data,0)
                liste3.append(str(cell_data))
            liste_risque_defaut.append(liste3)
    dataDictionary = {
        'liste_risque_defaut' : liste_risque_defaut ,
        'liste_engagement_securite' : liste_engagement_securite ,
        'part_prime_courtier' : part_prime_courtier ,
        'part_prime_courtier_retro' : part_prime_courtier_retro ,
        'liste_loss_ratio' : liste_loss_ratio ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    liste_branches = get_branches_cet('classique')
    liste_branches.pop(0)
    context = {
        'data' : dataJSON ,
        'paginate': True ,
        'liste_branches' : liste_branches
    }
    return render (request , 'main/templates/kri.html',context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def kpi_view(request) :
    liste_taux_retention = []
    liste_evo_ca = []
    liste_pourcentage_ca = []
    liste_pour_ca_portfolio = []
    liste_marge_rea = []
    with connection.cursor() as cursor:

        cursor.execute("INSERT INTO DMY.CET_PDF_TEMP cpt SELECT rownum  AS id ,cm2.* FROM DMY.CET_M cm2 ")
    #Lors du 1er trimestre pour la retro, affecter aux PROV_SIN_CLO les PROV_SIN_OUV
    # pour eviter d'avoir une perte trop importante dans le net     
    #

        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)

        cursor.execute("delete from  DMY.CET_PDF_FAST_V2")

        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer

        cursor.execute(" SELECT ktr.*, ktr.TAUX_RETENTION FROM dmy.KPI_TAUX_RETENTION ktr ORDER BY ktr.BRANCHE   ")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 1 :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                liste1.append(str(cell_data))
            liste_taux_retention.append(liste1)
        cursor.execute(" SELECT kte.* ,kte.TAUX_EVOLUTION_CA FROM KPI_TAUX_EVOLUTION_CA kte ORDER BY kte.ZONE_CODE   ")
        page1= cursor.fetchall()
        for row_num, columns in enumerate(page1):
            liste2 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num == 1 :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                liste2.append(str(cell_data))
            liste_evo_ca.append(liste2)

        cursor.execute(" SELECT kp.*  FROM DMY.KPI_PCA_M kp")
        page2= cursor.fetchall()
        for row_num, columns in enumerate(page2):
            liste3 =[]
            for col_num, cell_data in enumerate(columns):
                liste3.append(str(cell_data))
            liste_pourcentage_ca.append(liste3)

        cursor.execute(" SELECT * FROM dmy.KPI_PCA_PORTFOLIO kpp ORDER BY kpp.BRANCHE ,kpp.ZONE_CODE , kpp.PORTFOLIO_TYPE ")
        page3= cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste4 =[]
            for col_num, cell_data in enumerate(columns):
                liste4.append(str(cell_data))
            liste_pour_ca_portfolio.append(liste4)
        cursor.execute("""  
                            SELECT * FROM 
                            (
                                SELECT 
                                    kmr.BRANCHE ,
                                    kmr.ZONE_CODE ,
                                    decode(kmr.TYPE_SOUSCRIPTION , 'A', 'A','R','B','N','C') AS TYPE_SOUSCRIPTION,
                                    kmr.RATIO_SINISTRALITE ,
                                    kmr.RATIO_COMMISSION ,
                                    kmr.MARGE_REASSURANCE ,
                                    kmr.VOLUME_AFFAIRES ,
                                    kmr.MARGE_REASSURANCE AS MARGE_REASSURANCE_2 ,
                                    kmr.RATIO_COMMISSION AS RATIO_COMMISSION_2 ,
                                    kmr.RATIO_SINISTRALITE AS RATIO_SINISTRALITE_2
                                FROM DMY.KPI_MARGE_REASSURANCE kmr
                            ) tt
                            ORDER BY tt.BRANCHE , tt.TYPE_SOUSCRIPTION , tt.ZONE_CODE
        """)
        page4= cursor.fetchall()
        for row_num, columns in enumerate(page4):
            liste5 =[]
            for col_num, cell_data in enumerate(columns):
                if ( col_num == 7) :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                if ( col_num == 8) :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                if ( col_num == 9) :
                    if cell_data < 0 :
                        cell_data = 0
                    if cell_data > 100 :
                        cell_data = 100
                liste5.append(str(cell_data))
            liste_marge_rea.append(liste5)
    dataDictionary = {
        'liste_marge_rea' : liste_marge_rea ,
        'liste_pour_ca_portfolio' : liste_pour_ca_portfolio ,
        'liste_pourcentage_ca' : liste_pourcentage_ca ,
        'liste_taux_retention' : liste_taux_retention ,
        'liste_evo_ca' : liste_evo_ca ,
    }
    # dump data
    liste_branches = get_branches_cet('classique')

    dataJSON = json.dumps(dataDictionary)
    context = {
        'data' : dataJSON ,
        'liste_branches' : liste_branches ,
    }
    return render (request , 'main/templates/kpi.html',context)

@login_required
def logout_view(request):
    logout(request)
    messages.success(request, 'Vous vous êtes déconnecté avec succès.')
    context = {
        'error' : 0 ,
         }
    return render(request, 'main/templates/login.html',context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def etatsexcel(request) :   
    liste_cet = []
    liste_directions = []
    row = []
    with connection.cursor() as cursor:
        #Get the info about CET
        cursor.execute("SELECT lc.ANNEE ,  lc.ID  FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC ")
        row = [(row1[0],row1[1]) for row1 in cursor.fetchall()]
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT * FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num > 0 :
                    liste1.append(str(cell_data))
            liste_cet.append(liste1)
    liste_directions = get_directions()
    date_formated = str (DATE_DEBUT_EXERCICE.strftime('%Y-%m-%d') )
    dataDictionary = {
        'liste_cet' : liste_cet ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    liste_branches = get_branches_cet("excel")
    context = {
        'data' : dataJSON ,
        'list_cet' : row ,
        'date_debut' : date_formated, 
        'liste_branches' : liste_branches ,
        'liste_directions' : liste_directions ,
         }
    return render(request, 'main/templates/etatsexcel.html', context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def etatsexcelerm(request) :   
    row = []
    with connection.cursor() as cursor:
        liste_cet =[]
        #Get the info about CET
        cursor.execute("SELECT lc.ANNEE ,  lc.ID  FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC ")
        row = [(row1[0],row1[1]) for row1 in cursor.fetchall()]
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT * FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num > 0 :
                    liste1.append(str(cell_data))
            liste_cet.append(liste1)

    date_formated = str (DATE_DEBUT_EXERCICE.strftime('%Y-%m-%d') )
    dataDictionary = {
        'liste_cet' : liste_cet ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    context = {
        'data' : dataJSON ,
        'list_cet' : row ,
        'date_debut' : date_formated, 
         }
    return render(request, 'main/templates/etats_excel_erm.html', context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def etatsexcelgen(request) :   

    row = []
    with connection.cursor() as cursor:
        liste_cet =[]
        liste_cedante = []
        #Get the info about CET
        cursor.execute("SELECT lc.ANNEE ,  lc.ID  FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC ")
        row = [(row1[0],row1[1]) for row1 in cursor.fetchall()]
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT * FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num > 0 :
                    liste1.append(str(cell_data))
            liste_cet.append(liste1)
        cursor.execute("SELECT bc.BROKER_CEDANT_CODE ,bc.BROKER_CEDANT_CODE||' '||bc.CEDANT_SHORT_NAME FROM RMS_TABLES.BROKER_CEDANT bc ORDER BY bc.BROKER_CEDANT_CODE ")
        page2= cursor.fetchall()
        for row_num, columns in enumerate(page2):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                    liste1.append(str(cell_data))
            liste_cedante.append(liste1)

    date_formated = str (DATE_DEBUT_EXERCICE.strftime('%Y-%m-%d') )
    dataDictionary = {
        'liste_cet' : liste_cet ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    context = {
        'data' : dataJSON ,
        'list_cet' : row ,
        'date_debut' : date_formated, 
        'liste_cedante' : liste_cedante ,
         }
    return render(request, 'main/templates/etats_excel_general.html', context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def index (request): 
    return render(request, 'main/templates/main.html')

@login_required
def redirectDev(request) : 
    return render(request, 'main/templates/inDevelopment.html')

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def pdf(request) : 

    type_souscriptions = ['A','R','N']
    zones = ['1','2','3','4','*','?']
    branches =get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    year = ''
    registerFont(TTFont('Calibri', 'Calibri.ttf')) # Just some font imports
    registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
    registerFont(TTFont('Arial', 'Arial.ttf')) 
    registerFont(TTFont('Georgia', 'Georgia.ttf')) 
    registerFont(TTFont('Verdana', 'Verdana.ttf')) 
    registerFont(TTFont('Tahoma', 'Tahoma.ttf'))

    #Initialiser les tables et les varaibles 
    with connection.cursor() as cursor:
        cursor.execute("INSERT INTO DMY.CET_PDF_TEMP cpt SELECT rownum  AS id ,cm2.* FROM DMY.CET_M cm2 ")

    #Lors du 1er trimestre pour la retro, affecter aux PROV_SIN_CLO les PROV_SIN_OUV
    # pour eviter d'avoir une perte trop importante dans le net     
    #
        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)
        cursor.execute("delete from CET_PDF_FAST_V2")
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        UNDERWRITING_YEAR = row2[0]
        year = str(UNDERWRITING_YEAR)
        cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
        cursor.execute("SELECT  count(*)  FROM  (SELECT  DISTINCT spfv.TYPE_SOUSCRIPTION , SPFV .BRANCHE , SPFV .ZONE_CODE FROM DMY.CET_PDF_FAST_V2 spfv )")
        row = cursor.fetchone()
        nombre_pages = row[0]


    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y %H-%M-%S")
    name_pdf = 'CET_PROVISOIRE_'+dt_string+'.pdf'
    p = canvas.Canvas("pdf/"+name_pdf)
    

    #Creating THE PAGE DE GARDE
    p.setPageSize(portrait(A4))
    p.setFillColorRGB(84/255,119/255,157/255)

    # THE RECTANGLE AT THE TOP OF THE PAGE
    p.rect(0,712,600,130, fill=1 ,stroke=False) 

    # THE RECTANGLE AT THE MIDDLE OF THE PAGE
    p.setFillColorRGB(156/255,158/255,159/255)
    p.rect(0,132,600,580, fill=1 ,stroke=False)
    
    #THE TEXTE AT THE TOP OF THE PAGE 
    p.setFillColorRGB(255/255,255/255,255/255)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30, 790, "COMPTE D'EXPLOITATION TECHNIQUE")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(30, 770, "COMPAGNIE CENTRALE DE REASSURANCE" )
    p.drawString(30, 750, str(exercice) )
    #THE IMAGE AT AND THE SLOGAN AT THE BOTTOM OF THE PAGE 
    Image =ImageReader('img/logoShort.png')
    p.drawImage(Image,420,30, width=114,height=70,mask='auto')
    p.setFillColorRGB(84/255,119/255,157/255)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, 50, "Serving your challenges, Supporting your activity" )

    #THE YEAR AT THE MIDDLE OF THE PAGE
    p.setFont("Helvetica", 210)
    p.drawString(90, 180, str(UNDERWRITING_YEAR)  )

    p.showPage()
    #THE SOMMAIRE 
    p.setFont("Helvetica", 25)
    p.setFillColorRGB(84/255,119/255,157/255)

    page_sommaire = 1 
    
    souscription = ' '
    for k1 in type_souscriptions :
        x=158
        y=700
        
        p.setFillColorRGB(84/255,119/255,157/255)
        p.setFont("Helvetica", 15)
        p.drawString(45, 770, "SOMMAIRE       "+str(exercice)+" "+str(UNDERWRITING_YEAR) )
        p.setFont("Helvetica", 10)
        p.drawString(x, y+30, decoderSouscriton(k1))
        y =y -20
        branches_deja_fait =[]
        for j1 in branches :
            for i1 in zones :
                condition1 = True
                condition2 = True
                p.setFillColorRGB(0/255,0/255,0/255)
                page = Pdf_fast_v2.objects.filter(type_souscription= k1).filter(branche=j1).filter(zone_code = i1)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :     
                    condition2= False
                if (condition1 == True) or (condition2 == True) : 
                    if k1 == 'A' and j1 not in branches_deja_fait :
                        branches_deja_fait.append(j1)
                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), 
                                                 ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                        
                        
                    elif k1 =='R' or k1 =='N' :

                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data ,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                    page_sommaire = page_sommaire + 1 
        p.showPage()       

    #PRINT THE TABLES 
    p.setPageSize(landscape(A4))

    
    
    
    #Condition to check if a page is empty
    condition1 = True
    condition2 = True
    #table_pdf = Pdf_fast_v2.objects.all()
    page_en_cours = 1

    for k in type_souscriptions :
        for j in branches :
            for i in zones :

                #Condition to check if a page is empty
                condition1 = True
                condition2 = True

                page = Pdf_fast_v2.objects.filter(type_souscription= k).filter(branche=j).filter(zone_code = i)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    p1= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :
                    p2= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)     
                    condition2= False 
                

            # check if page is empty
                if (condition1 == True) or (condition2 == True) : 

            #Formating data with thousands separator and eliminate the 0.00 and replace it with empty String
                    ligne1 = [   p1.sinistre_1 , p2.sinistre_1 , (p1.sinistre_1 + p2.sinistre_1) ]
                    ligne1formated = ['SINISTRES REGLES ET RACHAT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne1]
                    ligne2 = [  p1.prov_sin_ouv_2,  p2.prov_sin_ouv_2, (p1.prov_sin_ouv_2+ p2.prov_sin_ouv_2) ]
                    ligne2formated = ['PROVISION SINISTRE OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne2]
                    ligne3 = [   p1.prov_sin_clo_3,  p2.prov_sin_clo_3 ,(p1.prov_sin_clo_3+ p2.prov_sin_clo_3) ]
                    ligne3formated = ['PROVISION SINISTRE CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne3]
                    ligne4 = [  p1.SINISTRES_COMP_EXE_4,  p2.SINISTRES_COMP_EXE_4 ,(p1.SINISTRES_COMP_EXE_4 +p2.SINISTRES_COMP_EXE_4)]
                    ligne4formated = ['SINISTRES DE COMPETENCE EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne4]
                    ligne6 =  [   p1.les_charges_6 ,  p2.les_charges_6 ,(p1.les_charges_6+p2.les_charges_6)]
                    ligne6formated = ['COMMISSIONS ET CHARGES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne6]
                    ligne8 = [   p1.courtage_8,  p2.courtage_8,(p1.courtage_8+p2.courtage_8)]
                    ligne8formated = ['COURTAGE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if '{:,.2f}'.format(elem) != '0.00' else '' for elem in ligne8]
                    ligne9 = [   p1.prov_egal_ouv_24,  p2.prov_egal_ouv_24, (p1.prov_egal_ouv_24+ p2.prov_egal_ouv_24)]
                    ligne9formated = ['PROVISIONS EGALISATION OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne9]
                    ligne10 = [   p1.prov_equi_ouv_25 ,  p2.prov_equi_ouv_25, (p1.prov_equi_ouv_25+ p2.prov_equi_ouv_25) ]
                    ligne10formated = ['PROVISIONS EQUILIBRAGE OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00'  else '' for elem in ligne10]
                    ligne11 = [  p1.prov_egal_clo_26 ,  p2.prov_egal_clo_26,(p1.prov_egal_clo_26 +p2.prov_egal_clo_26) ]
                    ligne11formated = ['PROVISIONS EGALISATION CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne11]
                    ligne12 =[  p1.prov_equi_clo_27,  p2.prov_equi_clo_27,(p1.prov_equi_clo_27+p2.prov_equi_clo_27)]
                    ligne12formated = ['PROVISIONS EQUILIBRAGE CLOTURE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne12]
                    ligne13 = [  p1.prov_egal_clo_ouv_22 ,  p2.prov_egal_clo_ouv_22,(p1.prov_egal_clo_ouv_22+p2.prov_egal_clo_ouv_22)]
                    ligne13formated = ['PROVISIONS EGALISATION CLOTURE-OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne13]
                    ligne14 = [   p1.prov_equi_clo_ouv_23 ,  p2.prov_equi_clo_ouv_23, (p1.prov_equi_clo_ouv_23+p2.prov_equi_clo_ouv_23)]
                    ligne14formated = ['PROVISIONS EQUILIBRAGE CLOTURE-OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne14]
                    ligne15 = [   p1.total_9 ,  p2.total_9 ,(p1.total_9+p2.total_9)]
                    ligne15formated = ['TOTAL']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne15]
                    ligne16 = [  p1.primes_encaiss_10 ,  p2.primes_encaiss_10,(p1.primes_encaiss_10+p2.primes_encaiss_10)]
                    ligne16formated = ['PRIMES EMISES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne16]
                    ligne17 = [  p1.ent_prt_prime_11, p2.ent_prt_prime_11,(p1.ent_prt_prime_11 + p2.ent_prt_prime_11)]
                    ligne17formated = ['ENTREES PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne17]
                    ligne18 = [  p1.sor_prt_prime_12,  p2.sor_prt_prime_12,(p1.sor_prt_prime_12+p2.sor_prt_prime_12)]
                    ligne18formated = ['SORTIE PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne18]
                    ligne19 = [  p1.primes_nettes_13 ,  p2.primes_nettes_13,(p1.primes_nettes_13+p2.primes_nettes_13)]
                    ligne19formated = ['PRIMES NETTES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne19]
                    ligne20 = [  p1.primes_nettes_ann_16 ,   p2.primes_nettes_ann_16 ,(p1.primes_nettes_ann_16+p2.primes_nettes_ann_16)]
                    ligne20formated = ['PRIMES NETTES ANNUELLES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne20]
                    ligne21 = [  p1.prov_pri_ouv_17,   p2.prov_pri_ouv_17,(p1.prov_pri_ouv_17+p2.prov_pri_ouv_17)]
                    ligne21formated = ['PROVISION PRIME OUVERTURE']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne21]
                    ligne22 = [  p1.prov_prim_clo_18,  p2.prov_prim_clo_18,(p1.prov_prim_clo_18+p2.prov_prim_clo_18)]
                    ligne22formated = ['PROVISION PRIME CLOTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne22]
                    ligne23 = [  p1.primes_acquises_exe_19 ,  p2.primes_acquises_exe_19,(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19)]
                    ligne23formated = ['PRIMES ACQUISES EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne23]
                    ligne24 = [  p1.BENEFICE_PERTE_20 ,  p2.BENEFICE_PERTE_20,(p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)]
                    ligne24formated = ['BENEFICE/PERTE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne24]
                    

        # Format data to eliminate the 0.00 and the -0.00 and replace it with empty String
                    ligne1SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne1formated]
                    ligne2SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne2formated]
                    ligne3SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne3formated]
                    ligne4SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne4formated]
                    ligne6SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne6formated]
                    ligne8SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne8formated]
                    ligne9SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne9formated]
                    ligne10SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne10formated]
                    ligne11SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne11formated]
                    ligne12SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne12formated]
                    ligne13SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne13formated]
                    ligne14SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne14formated]
                    ligne15SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne15formated]
                    ligne16SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne16formated]
                    ligne17SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne17formated]
                    ligne18SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne18formated]
                    ligne19SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne19formated]
                    ligne20SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne20formated]
                    ligne21SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne21formated]
                    ligne22SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne22formated]
                    ligne23SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne23formated]
                    ligne24SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne24formated]


        #Reset values of totals
                    total_5 = 0
                    total_21 = 0
                    total_7 = 0
        # SPECIAL CALCULS WHITH DIVISIONS THE 5 7 AND 21 
                    if ((p1.primes_encaiss_10+p2.primes_encaiss_10) !=0 ) : 
                        total_7 = abs (100*(p1.les_charges_6+p2.les_charges_6)/(p1.primes_encaiss_10+p2.primes_encaiss_10))
                    if ( (p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) !=0 ) :
                        total_21 = abs ( 100*( (p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)/(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) ) )
                    if ( ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) ) != 0  ) :
                        total_5 = abs ( 100*( (p1.sinistre_1+p2.sinistre_1) -(p1.prov_sin_ouv_2+p2.prov_sin_ouv_2)+(p1.prov_sin_clo_3+p2.prov_sin_clo_3) )/ ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) )    )
        # Formating the special lines            
                    
                    ligne5  =  [p1.SINISTRES_PRIMES_ACQU_5 ,  p2.SINISTRES_PRIMES_ACQU_5 ,total_5]
                    ligne5formated = ['SINISTRES/PRIMES ACQUISES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne5]  
                    ligne5SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne5formated]
                    
                    ligne7 = [  p1.commissions_primes_7,  p2.commissions_primes_7,total_7]
                    ligne7formated = ['COMMISSIONS/PRIMES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne7]
                    ligne7SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne7formated]

                    ligne25 = [  p1.rn_pra_21,  p2.rn_pra_21,total_21]
                    ligne25formated = ['RN/PRA  %']+[ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne25]
                    ligne25SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne25formated]

                    data = [
                        ['BRANCHE '+decoderBranche(j), 'TRAITES', 'FACULTATIVES', 'TOTAL'],
                        ligne1SuperFormated,
                        ligne2SuperFormated,
                        ligne3SuperFormated,
                        ligne4SuperFormated,
                        ligne5SuperFormated,
                        ligne6SuperFormated,
                        ligne7SuperFormated,
                        ligne8SuperFormated,
                        ligne9SuperFormated,
                        ligne10SuperFormated,
                        ligne11SuperFormated,
                        ligne12SuperFormated,        
                        ligne13SuperFormated,
                        ligne14SuperFormated,
                        ligne15SuperFormated,
                        ligne16SuperFormated,
                        ligne17SuperFormated,        
                        ligne18SuperFormated,
                        ligne19SuperFormated,
                        ligne20SuperFormated,
                        ligne21SuperFormated,
                        ligne22SuperFormated,
                        ligne23SuperFormated,
                        ligne24SuperFormated,
                        ligne25SuperFormated]
                        
                    width = 400
                    height = 100
                    
        #DEFINE THE STYLING OF THE DATA TABLE

                    p.setFont('Times-Roman', 10)
                    f = Table(data ,colWidths=[252,140,140,140], 
                                    rowHeights=[18,25,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15])
                    f.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                        ('ALIGN', (0,0), (0,25), 'LEFT'),
                        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                        ('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,0), (-1,0), 1.4, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,1), (-1,24), 0.7, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,25), (-1,25), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('VALIGN',(0,0),(3,0),'MIDDLE'),
                        ('VALIGN',(0,2),(-1,-1),'MIDDLE'),
                        ('BACKGROUND',(3,0),(3,25),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('BACKGROUND',(0,15),(3,15),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('TEXTCOLOR',(0,0),(3,0),colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('TEXTCOLOR',(0,1),(-1,-1),colors.Color(red=(0/255),green=(0/255),blue=(0/255))),
                        ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                        ('FONTSIZE', (1,1), (-1, -1), 10), 
                        ]))
                    f.wrapOn(p, width, height)
                    f.drawOn(p,76, 40) 

        #PRINT THE SOUSCRIPTION AND ZONE
                    p.setFont("Helvetica-Bold", 13)
                    p.setFillColorRGB(84/255,119/255,157/255) #choose your font colour
                    zone_texte = ''
                    if k == 'A' : 
                        zone_texte = decoderZone(i)
                    
                    p.drawString(82, 480, decoderSouscriton(k)+' '+ zone_texte)

                #PRINT THE OTHER LINES 
                    p.setFont("Helvetica-Bold", 17)
                    p.drawString(82, 550, "COMPTE D'EXPLOITATION TECHNIQUE" )
                    p.setFont("Helvetica", 11)
                    p.drawString(82, 530, "PAR BRANCHES ET REGIONS EN DINARS ALGERIENS" )
                    p.setFont("Helvetica", 9)

                #PRINT THE IMAGE LOGO and OTHER STUFF
                    p.setFillColorRGB(0/255,0/255,0/255)
                    #p.drawString(82, 450, "EN MILLION DE DINARS")
                    p.drawString(688, 450, "ANNEE "+year)
                    Image =ImageReader('img/logo02.png')
                    p.drawImage(Image,452,525, width=297,height=52,mask='auto')   

                # PRINT THE PAGE NUMBER AND THE DATE
                    p.drawString(688, 23,"PAGE "+str(page_en_cours)+"/"+str(nombre_pages))
                    today = date.today()
                    d1 = today.strftime("%d/%m/%Y %H-%M-%S")
                    p.drawString(82, 23,dt_string.replace('_','/'))
                    page_en_cours = page_en_cours+1

                #GO TO THE NEXT PAGE

                    p.showPage()
    # Close the PDF object cleanly, and we're done.

    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.

    buffer.seek(0)
    # GET THE STATUS OF RMS SYSTEM
    with connection.cursor() as cursor:
        cursor.execute(" SELECT scp.IS_RMS_ACTIVE FROM dmy.CET_PARAMETRES scp ")
        row4 = cursor.fetchone()
        rms_active = row4[0]

    context = {
        'name_pdf': name_pdf ,
        'rms_active' : rms_active ,
        'origine' : 'pdf'
    }
    #return FileResponse(buffer, as_attachment=True, filename='hello.pdf')
    
    return render(request, 'main/templates/pdf.html' , context )

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def pdftakaful(request) : 

    type_souscriptions = ['A','R','N']
    zones = ['1','2','3','4','*','?']
    branches =get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    year = ''
    registerFont(TTFont('Calibri', 'Calibri.ttf')) # Just some font imports
    registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
    registerFont(TTFont('Arial', 'Arial.ttf')) 
    registerFont(TTFont('Georgia', 'Georgia.ttf')) 
    registerFont(TTFont('Verdana', 'Verdana.ttf')) 
    registerFont(TTFont('Tahoma', 'Tahoma.ttf'))

    #Initialiser les tables et les varaibles 
    with connections['takaful'].cursor() as cursor:
        cursor.execute("INSERT INTO DOP.CET_PDF_TEMP cpt SELECT rownum  AS id ,cm2.* FROM REAPP.CET_M cm2 ")
        cursor.execute("delete from dop.CET_PDF_FAST_TAKAFUL")
        cursor.execute("SELECT scp.CET_EN_COURS FROM REAPP.STORE_CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM REAPP.STORE_CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        UNDERWRITING_YEAR = row2[0]
        year = str(UNDERWRITING_YEAR)
        cursor.execute("SELECT scp.EXERCICE FROM REAPP.STORE_CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
        cursor.callproc("DOP.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
        cursor.execute("SELECT  count(*)  FROM  (SELECT  DISTINCT spfv.TYPE_SOUSCRIPTION , SPFV .BRANCHE , SPFV .ZONE_CODE FROM dop.CET_PDF_FAST_TAKAFUL spfv )")
        row = cursor.fetchone()
        nombre_pages = row[0]


    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y %H-%M-%S")
    name_pdf = 'CET_TAKAFUL_PROVISOIRE_'+dt_string+'.pdf'
    p = canvas.Canvas("pdf/"+name_pdf)
    

    #Creating THE PAGE DE GARDE
    p.setPageSize(portrait(A4))
    p.setFillColorRGB(84/255,119/255,157/255)

    # THE RECTANGLE AT THE TOP OF THE PAGE
    p.rect(0,712,600,130, fill=1 ,stroke=False) 

    # THE RECTANGLE AT THE MIDDLE OF THE PAGE
    p.setFillColorRGB(156/255,158/255,159/255)
    p.rect(0,132,600,580, fill=1 ,stroke=False)
    
    #THE TEXTE AT THE TOP OF THE PAGE 
    p.setFillColorRGB(255/255,255/255,255/255)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30, 790, "COMPTE D'EXPLOITATION TECHNIQUE RETAKAFUL")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(30, 770, "COMPAGNIE CENTRALE DE REASSURANCE")
    p.drawString(30, 750, str(exercice) )
    #THE IMAGE AT AND THE SLOGAN AT THE BOTTOM OF THE PAGE 
    Image =ImageReader('img/logoShort.png')
    p.drawImage(Image,420,30, width=114,height=70,mask='auto')
    p.setFillColorRGB(84/255,119/255,157/255)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, 50, "Serving your challenges, Supporting your activity" )

    #THE YEAR AT THE MIDDLE OF THE PAGE
    p.setFont("Helvetica", 210)
    p.drawString(90, 180, str(UNDERWRITING_YEAR)  )

    p.showPage()
    #THE SOMMAIRE 
    p.setFont("Helvetica", 25)
    p.setFillColorRGB(84/255,119/255,157/255)

    page_sommaire = 1 
    
    souscription = ' '
    for k1 in type_souscriptions :
        x=158
        y=700
        
        p.setFillColorRGB(84/255,119/255,157/255)
        p.setFont("Helvetica", 15)
        p.drawString(45, 770, "SOMMAIRE       "+str(exercice)+" "+str(UNDERWRITING_YEAR) )
        p.setFont("Helvetica", 10)
        p.drawString(x, y+30, decoderSouscriton(k1))
        branches_deja_fait =[]
        y =y -20
        for j1 in branches :
            for i1 in zones :
                condition1 = True
                condition2 = True
                p.setFillColorRGB(0/255,0/255,0/255)
                page = Pdf_fast_takaful.objects.using('takaful').filter(type_souscription= k1).filter(branche=j1).filter(zone_code = i1)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :     
                    condition2= False
                if (condition1 == True) or (condition2 == True) : 
                    if k1 == 'A' and j1 not in branches_deja_fait :
                        branches_deja_fait.append(j1) 
                        data = [[ ' '+decoderBrancheTakaful(j1) ,str(page_sommaire) ]]
                        f = Table(data,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), 
                                                 ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                        
                        
                    elif k1 =='R' or k1 =='N' :

                        data = [[ ' '+decoderBrancheTakaful(j1) ,str(page_sommaire) ]]
                        f = Table(data ,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                ('FONTSIZE', (0,0), (-1, -1), 9), ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                    page_sommaire = page_sommaire + 1 
        p.showPage()       

    #PRINT THE TABLES 
    p.setPageSize(landscape(A4))

        
    #Condition to check if a page is empty
    condition1 = True
    condition2 = True
    #table_pdf = Pdf_fast_takaful.objects.using('takaful').all()
    page_en_cours = 1

    for k in type_souscriptions :
        for j in branches :
            for i in zones :

                #Condition to check if a page is empty
                condition1 = True
                condition2 = True

                page = Pdf_fast_takaful.objects.using('takaful').filter(type_souscription= k).filter(branche=j).filter(zone_code = i)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    p1= Pdf_fast_takaful(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0,wakala_22=0)   
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :
                    p2= Pdf_fast_takaful(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0,wakala_22=0)     
                    condition2= False 
                

            # check if page is empty
                if (condition1 == True) or (condition2 == True) : 

            #Formating data with thousands separator and eliminate the 0.00 and replace it with empty String
                    ligne1 = [   p1.sinistre_1 , p2.sinistre_1 , (p1.sinistre_1 + p2.sinistre_1) ]
                    ligne1formated = ['SINISTRES REGLES ET RACHAT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne1]
                    ligne2 = [  p1.prov_sin_ouv_2,  p2.prov_sin_ouv_2, (p1.prov_sin_ouv_2+ p2.prov_sin_ouv_2) ]
                    ligne2formated = ['PROVISION SINISTRE OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne2]
                    ligne3 = [   p1.prov_sin_clo_3,  p2.prov_sin_clo_3 ,(p1.prov_sin_clo_3+ p2.prov_sin_clo_3) ]
                    ligne3formated = ['PROVISION SINISTRE CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne3]
                    ligne4 = [  p1.SINISTRES_COMP_EXE_4,  p2.SINISTRES_COMP_EXE_4 ,(p1.SINISTRES_COMP_EXE_4 +p2.SINISTRES_COMP_EXE_4)]
                    ligne4formated = ['SINISTRES DE COMPETENCE EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne4]
                    ligne6 =  [   p1.les_charges_6 ,  p2.les_charges_6 ,(p1.les_charges_6+p2.les_charges_6)]
                    ligne6formated = ['COMMISSIONS ET CHARGES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne6]
                    ligne6_1 =  [   p1.wakala_22 ,  p2.wakala_22 ,(p1.wakala_22+p2.wakala_22)]
                    ligne6_1formated = ['WAKALA'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne6_1]
                    ligne8 = [   p1.courtage_8,  p2.courtage_8,(p1.courtage_8+p2.courtage_8)]
                    ligne8formated = ['COURTAGE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if '{:,.2f}'.format(elem) != '0.00' else '' for elem in ligne8]
                    ligne9 = [   p1.prov_egal_ouv_24,  p2.prov_egal_ouv_24, (p1.prov_egal_ouv_24+ p2.prov_egal_ouv_24)]
                    ligne9formated = ['PROVISIONS EGALISATION OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne9]
                    ligne10 = [   p1.prov_equi_ouv_25 ,  p2.prov_equi_ouv_25, (p1.prov_equi_ouv_25+ p2.prov_equi_ouv_25) ]
                    ligne10formated = ['PROVISIONS EQUILIBRAGE OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00'  else '' for elem in ligne10]
                    ligne11 = [  p1.prov_egal_clo_26 ,  p2.prov_egal_clo_26,(p1.prov_egal_clo_26 +p2.prov_egal_clo_26) ]
                    ligne11formated = ['PROVISIONS EGALISATION CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne11]
                    ligne12 =[  p1.prov_equi_clo_27,  p2.prov_equi_clo_27,(p1.prov_equi_clo_27+p2.prov_equi_clo_27)]
                    ligne12formated = ['PROVISIONS EQUILIBRAGE CLOTURE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne12]
                    ligne13 = [  p1.prov_egal_clo_ouv_22 ,  p2.prov_egal_clo_ouv_22,(p1.prov_egal_clo_ouv_22+p2.prov_egal_clo_ouv_22)]
                    ligne13formated = ['PROVISIONS EGALISATION CLOTURE-OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne13]
                    ligne14 = [   p1.prov_equi_clo_ouv_23 ,  p2.prov_equi_clo_ouv_23, (p1.prov_equi_clo_ouv_23+p2.prov_equi_clo_ouv_23)]
                    ligne14formated = ['PROVISIONS EQUILIBRAGE CLOTURE-OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne14]
                    ligne15 = [   p1.total_9 ,  p2.total_9 ,(p1.total_9+p2.total_9)]
                    ligne15formated = ['TOTAL']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne15]
                    ligne16 = [  p1.primes_encaiss_10 ,  p2.primes_encaiss_10,(p1.primes_encaiss_10+p2.primes_encaiss_10)]
                    ligne16formated = ['FOND PARTICIPANT EMIS'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne16]
                    ligne17 = [  p1.ent_prt_prime_11, p2.ent_prt_prime_11,(p1.ent_prt_prime_11 + p2.ent_prt_prime_11)]
                    ligne17formated = ['ENTREES PORTEFEUILLE FOND PARTICIPANT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne17]
                    ligne18 = [  p1.sor_prt_prime_12,  p2.sor_prt_prime_12,(p1.sor_prt_prime_12+p2.sor_prt_prime_12)]
                    ligne18formated = ['SORTIE PORTEFEUILLE FOND PARTICIPANT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne18]
                    ligne19 = [  p1.primes_nettes_13 ,  p2.primes_nettes_13,(p1.primes_nettes_13+p2.primes_nettes_13)]
                    ligne19formated = ['FOND PARTICIPANT NET']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne19]
                    ligne20 = [  p1.primes_nettes_ann_16 ,   p2.primes_nettes_ann_16 ,(p1.primes_nettes_ann_16+p2.primes_nettes_ann_16)]
                    ligne20formated = ['FOND PARTICIPANT NET ANNUELLES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne20]
                    ligne21 = [  p1.prov_pri_ouv_17,   p2.prov_pri_ouv_17,(p1.prov_pri_ouv_17+p2.prov_pri_ouv_17)]
                    ligne21formated = ['PROVISION FOND PARTICIPANT OUVERTURE']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne21]
                    ligne22 = [  p1.prov_prim_clo_18,  p2.prov_prim_clo_18,(p1.prov_prim_clo_18+p2.prov_prim_clo_18)]
                    ligne22formated = ['PROVISION FOND PARTICIPANT CLOTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne22]
                    ligne23 = [  p1.primes_acquises_exe_19 ,  p2.primes_acquises_exe_19,(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19)]
                    ligne23formated = ['FONDS PARTICIPANT ACQUIS EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne23]
                    ligne24 = [  p1.BENEFICE_PERTE_20 ,  p2.BENEFICE_PERTE_20,(p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)]
                    ligne24formated = ['BENEFICE/PERTE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne24]
                    

        # Format data to eliminate the 0.00 and the -0.00 and replace it with empty String
                    ligne1SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne1formated]
                    ligne2SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne2formated]
                    ligne3SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne3formated]
                    ligne4SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne4formated]
                    ligne6SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne6formated]
                    ligne6_1SuperFormated =[  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne6_1formated]
                    ligne8SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne8formated]
                    ligne9SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne9formated]
                    ligne10SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne10formated]
                    ligne11SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne11formated]
                    ligne12SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne12formated]
                    ligne13SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne13formated]
                    ligne14SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne14formated]
                    ligne15SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne15formated]
                    ligne16SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne16formated]
                    ligne17SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne17formated]
                    ligne18SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne18formated]
                    ligne19SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne19formated]
                    ligne20SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne20formated]
                    ligne21SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne21formated]
                    ligne22SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne22formated]
                    ligne23SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne23formated]
                    ligne24SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne24formated]

        #Reset values of totals
                    total_5 = 0
                    total_21 = 0
                    total_7 = 0
        # SPECIAL CALCULS WHITH DIVISIONS THE 5,7 AND 21 
                    if ((p1.primes_encaiss_10+p2.primes_encaiss_10) !=0 )   : 
                        total_7 = abs (100*(p1.les_charges_6+p2.les_charges_6 + p1.wakala_22+p2.wakala_22)/(p1.primes_encaiss_10+p2.primes_encaiss_10))
                    if ( (p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) !=0 ) :
                        total_21 = abs ( 100*( (p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)/(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) ) )
                    if ( ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) ) != 0  )   :
                        total_5 = abs (100* (   (p1.sinistre_1+p2.sinistre_1) -(p1.prov_sin_ouv_2+p2.prov_sin_ouv_2)+(p1.prov_sin_clo_3+p2.prov_sin_clo_3) )/ ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) ) )
        # Formating the special lines            
                    
                    ligne5  =  [p1.SINISTRES_PRIMES_ACQU_5 ,  p2.SINISTRES_PRIMES_ACQU_5 ,total_5]
                    ligne5formated = ['SINISTRES/FONDS PARTICIPANT ACQUIS  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne5]  
                    ligne5SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne5formated]
                    
                    ligne7 = [  p1.commissions_primes_7,  p2.commissions_primes_7,total_7]
                    ligne7formated = ['COMMISSIONS/FONDS PARTICIPANT  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne7]
                    ligne7SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne7formated]

                    ligne25 = [  p1.rn_pra_21,  p2.rn_pra_21,total_21]
                    ligne25formated = ['RN/PRA  %']+[ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne25]
                    ligne25SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne25formated]

                    data = [
                        ['BRANCHE '+decoderBrancheTakaful(j), 'TRAITES', 'FACULTATIVES', 'TOTAL'],
                        ligne1SuperFormated,
                        ligne2SuperFormated,
                        ligne3SuperFormated,
                        ligne4SuperFormated,
                        ligne5SuperFormated,
                        ligne6SuperFormated,
                        ligne6_1SuperFormated,
                        ligne7SuperFormated,
                        ligne8SuperFormated,
                        ligne9SuperFormated,
                        ligne10SuperFormated,
                        ligne11SuperFormated,
                        ligne12SuperFormated,        
                        ligne13SuperFormated,
                        ligne14SuperFormated,
                        ligne15SuperFormated,
                        ligne16SuperFormated,
                        ligne17SuperFormated,        
                        ligne18SuperFormated,
                        ligne19SuperFormated,
                        ligne20SuperFormated,
                        ligne21SuperFormated,
                        ligne22SuperFormated,
                        ligne23SuperFormated,
                        ligne24SuperFormated,
                        ligne25SuperFormated]
                        
                    width = 400
                    height = 100
                    
        #DEFINE THE STYLING OF THE DATA TABLE

                    p.setFont('Times-Roman', 10)
                    f = Table(data ,colWidths=[252,140,140,140], 
                                    rowHeights=[18,25,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15])
                    f.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                        ('ALIGN', (0,0), (0,25), 'LEFT'),
                        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                        ('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,0), (-1,0), 1.4, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,1), (-1,25), 0.7, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,26), (-1,26), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('VALIGN',(0,0),(3,0),'MIDDLE'),
                        ('VALIGN',(0,2),(-1,-1),'MIDDLE'),
                        ('BACKGROUND',(3,0),(3,26),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('BACKGROUND',(0,16),(3,16),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('TEXTCOLOR',(0,0),(3,0),colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('TEXTCOLOR',(0,1),(-1,-1),colors.Color(red=(0/255),green=(0/255),blue=(0/255))),
                        ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                        ('FONTSIZE', (1,1), (-1, -1), 10), 
                        ]))
                    f.wrapOn(p, width, height)
                    f.drawOn(p,76, 40) 

        #PRINT THE SOUSCRIPTION AND ZONE
                    p.setFont("Helvetica-Bold", 13)
                    p.setFillColorRGB(84/255,119/255,157/255) #choose your font colour
                    zone_texte = ''
                    if k == 'A' : 
                        zone_texte = decoderZone(i)
                    
                    p.drawString(82, 480, decoderSouscriton(k)+' '+ zone_texte)

                #PRINT THE OTHER LINES 
                    p.setFont("Helvetica-Bold", 17)
                    p.drawString(82, 550, "COMPTE D'EXPLOITATION TECHNIQUE" )
                    p.setFont("Helvetica", 11)
                    p.drawString(82, 530, "PAR BRANCHES ET REGIONS EN DINARS ALGERIENS" )
                    p.setFont("Helvetica", 9)

                #PRINT THE IMAGE LOGO and OTHER STUFF
                    p.setFillColorRGB(0/255,0/255,0/255)
                    #p.drawString(82, 450, "EN MILLION DE DINARS")
                    p.drawString(688, 470, "ANNEE "+year)
                    Image =ImageReader('img/logo02.png')
                    p.drawImage(Image,452,525, width=297,height=52,mask='auto')   

                # PRINT THE PAGE NUMBER AND THE DATE
                    p.drawString(688, 23,"PAGE "+str(page_en_cours)+"/"+str(nombre_pages))
                    today = date.today()
                    d1 = today.strftime("%d/%m/%Y %H-%M-%S")
                    p.drawString(82, 23,dt_string.replace('_','/'))
                    page_en_cours = page_en_cours+1

                #GO TO THE NEXT PAGE

                    p.showPage()
    # Close the PDF object cleanly, and we're done.

    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.

    buffer.seek(0)

    context = {
        'name_pdf': name_pdf
    }
    #return FileResponse(buffer, as_attachment=True, filename='hello.pdf')
    return render(request, 'main/templates/pdf.html' , context )

@login_required
def sauvegarderpdf (request ) :
    #Retrieve data 
    name_pdf = 'teste.pdf'
    if request.method == 'POST':
        name_pdf = request.POST.get('name_pdf')
    name = request.user.username
    error = -1 
    error_code = ''
    CET_EN_COURS = 0 
    with connection.cursor() as cursor:
        try : 
            cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
            row =cursor.fetchone()
            CET_EN_COURS = row[0]
            cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
            row2 =cursor.fetchone()
            DATE_DEBUT_EXERCICE = row2[0]
            cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp  ")
            row3 =cursor.fetchone()
            exercice = row3[0]
            cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM DMY.CET_PARAMETRES scp  ")
            row4 =cursor.fetchone()
            unserwriting_year = row4[0]
            cursor.execute("INSERT INTO dmy.CET_PERIODE VALUES (%s, %s , sysdate , %s  , %s, sysdate , %s)", 
                            [CET_EN_COURS,DATE_DEBUT_EXERCICE,exercice,unserwriting_year, name] )
            
        except Exception  as e :
            error = 1
            errorObj, = e.args
            error_code = errorObj.code
            if error_code == 1 : 
                messages.error(request , 'CET déjà insérer Code erreur : ORA-00001' )
            else : 
                messages.error(request , 'Erreur lors de la sauvegarde' )
        else :
            with connection.cursor() as cursor:
                cursor.callproc("DMY.INSERER_CET_V2",[CET_EN_COURS])
                # INITIALIZE THE IBNR TABLES 
                cursor.callproc("DMY.INITIALISER_IBNR")
            error = 0
            messages.success(request, 'Sauvegarde réussie')

    context = {
        'error_code': error_code ,
        'error' : error ,
        'name_pdf': name_pdf
    }
   
    return render(request, 'main/templates/pdf.html',context)
   
@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def genererpdf(request) : 

    #Initialiser les tables et les varaibles 
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
    
    date_formated = DATE_DEBUT_EXERCICE.strftime("%d/%m/%Y")
    today = date.today()
    today_formated = today.strftime("%d/%m/%Y")
    exercice_formated = str(exercice).lower()
    context = {
        'today' : today_formated,
        'date_debut': date_formated,
        'exercice' : exercice_formated
    }

    return render(request, 'main/templates/genererpdf.html' , context)

@login_required
def genererpdftakaful(request) : 

    #Initialiser les tables et les varaibles 
    with connections['takaful'].cursor() as cursor:
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM REAPP.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT scp.EXERCICE FROM REAPP.CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
    
    date_formated = DATE_DEBUT_EXERCICE.strftime("%d/%m/%Y")
    today = date.today()
    today_formated = today.strftime("%d/%m/%Y")
    exercice_formated = str(exercice).lower()
    context = {
        'today' : today_formated,
        'date_debut': date_formated,
        'exercice' : exercice_formated
    }

    return render(request, 'main/templates/genererpdftakaful.html' , context)

#USELESS CAN BE DELETED 
@login_required
def excelview(request):

    #THIS IS THE PROC THAT RETURNS THE EXCEL FILE

    
    #GET THE DATA
    with connection.cursor() as cursor:

        #Get the data  

        cursor.execute("SELECT * FROM DMY.cet_m")
        page = cursor.fetchall()



        cursor.execute("SELECT * FROM DMY.cet_m")
        entete= dictfetchall(cursor) 
        
        
        #Get the number of lines 

        cursor.execute("SELECT count(*) FROM DMY.cet_m" )
        row2 =cursor.fetchone()
        nb_lines = row2[0]



    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()

    # Even though the final file will be in memory the module uses temp
    # files during assembly for efficiency. To avoid this on servers that
    # don't allow temp files, for example the Google APP Engine, set the
    # 'in_memory' Workbook() constructor option as shown in the docs.
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet('Test')

    # Setup formats
    data_format = workbook.add_format({'num_format': 43 }) #'#,##0.00'
    number_format = workbook.add_format({'num_format': '#,##0'})
    exch_format = workbook.add_format({'num_format': '#,##0.00000'})
    year_format = workbook.add_format({'num_format': '####'})
    booked_format = workbook.add_format({'num_format': '####'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    # Write the data and format it
    for row_num, columns in enumerate(page):
        for col_num, cell_data in enumerate(columns):
            if isinstance(cell_data , datetimecomparaison.datetime) :
                worksheet.write(row_num+1, col_num, cell_data , date_format)
            elif entete[col_num] == 'UN'  or entete[col_num] == 'UNDERWRITING_YEAR':
                worksheet.write(row_num+1, col_num, cell_data , year_format)
            elif  'EXCH' in entete[col_num] :
                worksheet.write(row_num+1, col_num, cell_data , exch_format)
            elif  'BOOKED_TRANS' in entete[col_num]   :
                worksheet.write(row_num+1, col_num, cell_data , booked_format)
            elif  'NUMBER' in entete[col_num]   :
                worksheet.write(row_num+1, col_num, cell_data , number_format)
            elif isinstance(cell_data, (int, float, decimal.Decimal)) :
                worksheet.write(row_num+1, col_num, cell_data , data_format)
            else :
                worksheet.write(row_num+1, col_num, cell_data)

    #Get the number of colums 
    nb_columns = len(entete)
 
    #Get the fields name 
    i=0
    fields=[]
    while i < len(entete):
        fields.append({'header': str(entete[i])})     
        i += 1

    #Write the table and apply some styling
    worksheet.add_table(0,0,nb_lines,nb_columns-1, {'style': 'Table Style Light 9', 
                                                #'banded_rows': False ,
                                                'banded_columns': True ,
                                                 'columns' : fields })

    # Resize the columns
    worksheet.set_column(0,nb_columns, 20)  # Columns F-H width set to 30.

    worksheet = workbook.add_worksheet('Test02')

    # Close the workbook before sending the data.
    workbook.close()

    # Rewind the buffer.
    output.seek(0)

    # Set up the Http response.
    filename = 'test.xlsx'
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response 

@login_required
def excelview2(request):
    #
    # ALWAYS USE THE FUNCTION TO_DATE OF ORACLE WHEN PLAYING WHIT DATES BECAUSE CX_ORACLE USES YYYY/MM/DD
    # AND THE IDE CAN USE THE DD/MM/YYYY FORMAT 
    #
    #THIS IS THE PROC THAT RETURNS THE EXCEL FILE
    #num_cet ="0"
    if request.method == 'GET':
        annee = request.GET.get('annee')
        code_view = request.GET.get('code_view')
        trim = request.GET.get('trim')
        date_fin = request.GET.get('date_fin')
        tr  = request.GET.get('tr')
        branche = request.GET.get('branche')
        direction = request.GET.get('direction')
        cedante = request.GET.get('cedante')
        brocker = request.GET.get('brocker')
        participant = request.GET.get('participant')

    #Initialiser les tables et les varaibles 
    condition =''

    if tr == 'on' :
        date_fin = datetimecomparaison.date.today() + datetimecomparaison.timedelta(days=1) 
        date_fin = str(date_fin)
    #CONDITION ON THE BRANCHE
    if branche is None : 
        condition_branche = " "
    else :
        if branche != '?' : 
            condition_branche = " cea.BRANCH_NAME ="+"'"+branche+"'"
    #CONDITION ON THE DIRECTION
    if direction  is None : 
        condition_direction = " "
    else :
        if direction != '?' :
            condition_direction = get_sub_profit_center_code(direction)
    #POUR LE CAS DES ETATS ERM ET GENERAL 
    if (branche is not None) and (direction is not None) : 
        if (branche != '?') and (direction != '?') : 
            condition = ' where ' + condition_branche + ' and ' + condition_direction
        if (branche == '?') and (direction != '?') : 
            condition = ' where '  + condition_direction
        if (branche != '?') and (direction == '?') : 
            condition = ' where ' + condition_branche 
    #GET THE DATA
    with connection.cursor() as cursor:
        #CASE FOR EACH CONFIG 
        if code_view.startswith('03') :
            cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (%s,null,null,null,null,null)",[participant])
        if code_view.startswith('02') :
            cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (%s,%s,null,null,null,null)",[cedante, brocker])
        if code_view.startswith('01') :
            cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (null,null,%s,null,null,null)",[annee])
        if code_view.startswith('00') : # CASE WHERE WE NEED 1 NUMERICAL PARAMETER WICH IS THE NUM_CET WE ADDES THE CET DATES FOR 
            #AFTER THE MODIFICATIONS MADE TO THE VIEWS THE PARAMETER num_cet IS USELESS IN ETAT_EXCEL_PARAM
            #FETCH THE NUM CET 
            request1 = 'SELECT lc."'+trim+'" FROM DMY.LISTE_CET lc WHERE lc.ANNEE = %s'
            cursor.execute(request1,[annee])
            row23 =cursor.fetchone()
            num_cet = row23[0]
            dates = get_dates_cet(num_cet)
            #INSERT THE VARAIBLES INTO THE TEMPORARY TABLE
            cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (null,null,%s,null,%s,%s)",[num_cet , dates[0] , dates[1] ])
        if code_view.startswith('DT') :# CASE WHERE WE NEED 1 DATE PARAMETER
            cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp " )
            one_row = cursor.fetchone()
            date_debut = one_row[0]
            cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (null,null,null,null,%s,%s)",[date_debut,date_fin])
     
        #Get the fields names
        view = decoderCodeView(code_view , annee )

        cursor.execute("SELECT * FROM "+ view + condition)
        entete= dictfetchall(cursor) 
        #Get the data 
        #cursor.execute("SELECT * FROM "+view + condition)
        page = cursor.fetchall()
        #Get the number of lines 
        #cursor.execute("SELECT count(*) FROM "+view + condition)
        #row2 =cursor.fetchone()
        #nb_lines = row2[0]
        i= 0
        for row_num, columns in enumerate(page):
            i = i+1 
        nb_lines = i 


    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()

    # Even though the final file will be in memory the module uses temp
    # files during assembly for efficiency. To avoid this on servers that
    # don't allow temp files, for example the Google APP Engine, set the
    # 'in_memory' Workbook() constructor option as shown in the docs.
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()

    # Setup formats
    data_format = workbook.add_format({'num_format': 43 }) #'#,##0.00'
    number_format = workbook.add_format({'num_format': '#,##0'})
    exch_format = workbook.add_format({'num_format': '#,##0.00000'})
    year_format = workbook.add_format({'num_format': '####'})
    booked_format = workbook.add_format({'num_format': '####'})
    date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
    # Write the data and format it
    for row_num, columns in enumerate(page):
        for col_num, cell_data in enumerate(columns):
            if isinstance(cell_data , datetimecomparaison.datetime) :
                worksheet.write(row_num+1, col_num, cell_data , date_format)
            elif entete[col_num] == 'UN'  or entete[col_num] == 'UNDERWRITING_YEAR':
                worksheet.write(row_num+1, col_num, cell_data , year_format)
            elif  'EXCH' in entete[col_num] :
                worksheet.write(row_num+1, col_num, cell_data , exch_format)
            elif  'BOOKED_TRANS' in entete[col_num]   :
                worksheet.write(row_num+1, col_num, cell_data , booked_format)
            elif  'NUMBER' in entete[col_num]   :
                worksheet.write(row_num+1, col_num, cell_data , number_format)
            elif isinstance(cell_data, (int, float, decimal.Decimal)) :
                worksheet.write(row_num+1, col_num, cell_data , data_format)
            else :
                worksheet.write(row_num+1, col_num, cell_data)

    #Get the number of colums 
    nb_columns = len(entete)
 
    #Get the fields name 
    i=0
    fields=[]
    while i < len(entete):
        fields.append({'header': str(entete[i])})     
        i += 1

    #Write the table and apply some styling
    worksheet.add_table(0,0,nb_lines,nb_columns-1, {'style': 'Table Style Light 9', 
                                                #'banded_rows': False ,
                                                'banded_columns': True ,
                                                 'columns' : fields })

    # Resize the columns
    worksheet.set_column(0,nb_columns, 20)  # Columns F-H width set to 30.

    # Close the workbook before sending the data.
    workbook.close()

    # Rewind the buffer.
    output.seek(0)

    # Set up the Http response.
    filename = getNomFichier(code_view)+'.xlsx'
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response 

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def dashboard(request):
    branches =get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    #Get the data 
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]

        cursor.execute("SELECT scp.EXERCICE  FROM DMY.CET_PARAMETRES scp ")
        row3 =cursor.fetchone()
        semestre = row3[0]

        cursor.execute("INSERT INTO DMY.CET_PDF_TEMP cpt SELECT rownum  AS id ,cm2.* FROM DMY.CET_M cm2 ")
        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]

        cursor.execute("delete from CET_PDF_FAST_V2")
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
    date_formated = DATE_DEBUT_EXERCICE.strftime("%d/%m/%Y")

    #GETTING AND FORMATING  DATA NET 

    liste_net = []
    for br1 in branches : 
        page_net = Pdf_fast_v2.objects.filter(type_souscription= 'N').filter(branche=br1).filter(zone_code = '?')
        colonne1_test = page_net.filter(portfolio_type ='1')
        colonne2_test = page_net.filter(portfolio_type ='2')
        if colonne1_test.exists():
            colonne1_net = colonne1_test[0]
        else :
            colonne1_net= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   

        if colonne2_test.exists():
            colonne2_net = colonne2_test[0]
        else :
            colonne2_net= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   

        benef = colonne1_net.BENEFICE_PERTE_20 + colonne2_net.BENEFICE_PERTE_20
        benef_formated = '{:,.2f}'.format(benef).replace(',', ' ')
        sinistre = colonne1_net.sinistre_1 + colonne2_net.sinistre_1
        sinistre_formated =  '{:,.2f}'.format(sinistre).replace(',', ' ')
        prime = colonne1_net.primes_encaiss_10 + colonne2_net.primes_encaiss_10
        prime_formated = '{:,.2f}'.format(prime).replace(',', ' ')
        sap = colonne1_net.prov_sin_clo_3 + colonne2_net.prov_sin_clo_3
        sap_formated = '{:,.2f}'.format(sap).replace(',', ' ')
        net = [benef_formated,sinistre_formated,prime_formated,sap_formated]
        liste_net.append(net)
    #GETTING AND FORMATING DATA ACCEPTATION

    liste_acceptation= []
    for br in branches :
        page_acc = Pdf_fast_v2.objects.filter(type_souscription= 'A').filter(branche=br).filter(zone_code = '?')
        colonne1_test = page_acc.filter(portfolio_type ='1')
        colonne2_test = page_acc.filter(portfolio_type ='2')
        if colonne1_test.exists():
            colonne1_acc = colonne1_test[0]
        else :
            colonne1_acc= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   

        if colonne2_test.exists():
            colonne2_acc = colonne2_test[0]
        else :
            colonne2_acc= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   

        benef_acc = colonne1_acc.BENEFICE_PERTE_20 + colonne2_acc.BENEFICE_PERTE_20
        benef_formated_acc = '{:,.2f}'.format(benef_acc).replace(',', ' ')
        sinistre_acc = colonne1_acc.sinistre_1 + colonne2_acc.sinistre_1
        sinistre_formated_acc =  '{:,.2f}'.format(sinistre_acc).replace(',', ' ')
        prime_acc = colonne1_acc.primes_encaiss_10 + colonne2_acc.primes_encaiss_10
        prime_formated_acc = '{:,.2f}'.format(prime_acc).replace(',', ' ')
        sap_acc = colonne1_acc.prov_sin_clo_3 + colonne2_acc.prov_sin_clo_3
        sap_formated_acc = '{:,.2f}'.format(sap_acc).replace(',', ' ')
        acceptation = [benef_formated_acc,sinistre_formated_acc,prime_formated_acc,sap_formated_acc]    
        liste_acceptation.append(acceptation)


    #GETTING AND FORMATING DATA RETRO
    liste_retro = []
    for br2 in branches :
        page_retro = Pdf_fast_v2.objects.filter(type_souscription= 'R').filter(branche=br2).filter(zone_code = '?')
        colonne1_test = page_retro.filter(portfolio_type ='1')
        colonne2_test = page_retro.filter(portfolio_type ='2')
        if colonne1_test.exists():
            colonne1_retro = colonne1_test[0]
        else :
            colonne1_retro= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   

        if colonne2_test.exists():
            colonne2_retro = colonne2_test[0]
        else :
            colonne2_retro= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   
        benef_retro = colonne1_retro.BENEFICE_PERTE_20 + colonne2_retro.BENEFICE_PERTE_20
        benef_formated_retro = '{:,.2f}'.format(benef_retro).replace(',', ' ')
        sinistre_retro = colonne1_retro.sinistre_1 + colonne2_retro.sinistre_1
        sinistre_formated_retro =  '{:,.2f}'.format(sinistre_retro).replace(',', ' ')
        prime_retro = colonne1_retro.primes_encaiss_10 + colonne2_retro.primes_encaiss_10
        prime_formated_retro = '{:,.2f}'.format(prime_retro).replace(',', ' ')
        sap_retro = colonne1_retro.prov_sin_clo_3 + colonne2_retro.prov_sin_clo_3
        sap_formated_retro = '{:,.2f}'.format(sap_retro).replace(',', ' ')
        retro = [benef_formated_retro ,sinistre_formated_retro,prime_formated_retro,sap_formated_retro]
        liste_retro.append(retro)

    #GET DATE
    now = datetime.now()
    dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

    # create data dictionary
    dataDictionary = {
        'data_acceptation' :   liste_acceptation,
        'data_net' :   liste_net,
        'data_retro' :   liste_retro,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    #GET THE LIST OF BRANCHES 
    liste_branches = get_branches_cet('dashbord')
    context = {
        'data' : dataJSON,

        'acceptation' : liste_acceptation,
        'net' : liste_net ,
        'retro' : liste_retro,

        'semestre' : semestre ,
        'date' : dt_string ,
        'date_debut' : date_formated ,

        'liste_branches' : liste_branches ,
        }
    return render(request, 'main/templates/dashboard.html', context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.view_ibnr' ,raise_exception =True)
def view_ibnr(request):
    if request.method == 'GET':
        branche = request.GET.get('branche')
    context = ibnr_display(request,branche)
    return render(request, 'main/templates/ibnr.html' ,context )

@login_required
@permission_required('cet.view_ibnr' ,raise_exception =True)
def ibnr_save(request) :
    old_traite = ''
    old_fac = ''
    old_zone_algerie = ''
    old_zone_europe = ''
    old_zone_amerique_asie = ''
    old_zone_afrique = ''
    liste =[]
    if request.method == 'GET':
        branche = request.GET.get('branche_hidden')
        liste_zone = request.GET.getlist('zone')
        liste_sous = request.GET.getlist('souscription')
        for i in reversed (range(1,19)) :
            liste.append( (request.GET.get(str(i)),request.GET.get("year_"+str(i)))  )#(TAUX,UNDERWRINTING_YEAR)

    with connection.cursor() as cursor:
    #GETTING THE TYPE SOUSCRIPTION AND ZONES FOR THE BRANCHE
        cursor.execute("SELECT * FROM DMY.IBNR_PARAMETRE ip WHERE ip.BRANCHE =%s",[branche])
        rows1 = cursor.fetchone()
        old_traite = rows1[2]
        old_fac = rows1[3]
        old_zone_algerie = rows1[4]
        old_zone_europe = rows1[5]
        old_zone_amerique_asie = rows1[6]
        old_zone_afrique = rows1[7]
    #BUILDING THE REQUEST 
    #THE ZONES 

    request_set_zone=''
    if 'afrique' in liste_zone :
        new_zone_afrique = '1'
    else :
        new_zone_afrique = '0'
    if 'europe' in liste_zone :
        new_zone_europe = '1'
    else :
        new_zone_europe = '0'
    if 'asie_amerique' in liste_zone :
        new_zone_amerique_asie = '1'
    else :
        new_zone_amerique_asie = '0'
    #THE TYPE OF SOUSCRITPION
    request_set_sous=''
    if 'traite' in liste_sous :
        new_traite = '1'    #CAD TRAITE A ETE COCHE 
    else :
        new_traite = '0'    #CAD TRAITE N'A PAS ETE COCHE 
    if 'fac' in liste_sous :
        new_fac = '1'       #CAD FAC A ETE COCHE 
    else :
        new_fac = '0'       #CAD FAC N'A PAS ETE COCHE 
    request_set_sous = where_clause_portfolio (new_traite, new_fac)
    # UPDATE THE PARAMETERS OF THE BRANCHE 
    if new_traite != old_traite :
        with connection.cursor() as cursor:
            cursor.execute(" update DMY.IBNR_PARAMETRE ip set ip.TRAITE = %s WHERE ip.BRANCHE = %s  ", [new_traite,branche])
    if new_fac != old_fac :
        with connection.cursor() as cursor:
            cursor.execute(" update DMY.IBNR_PARAMETRE ip set ip.FAC = %s WHERE ip.BRANCHE = %s  ", [new_fac,branche])
    # UPDATE THE PARAMETERS OF THE ZONE
    if new_zone_afrique != old_zone_afrique :
        with connection.cursor() as cursor:
            cursor.execute(" update DMY.IBNR_PARAMETRE ip set ip.ZONE_AFRIQUE = %s WHERE ip.BRANCHE = %s  ", [new_zone_afrique,branche])
    if new_zone_europe != old_zone_europe :
        with connection.cursor() as cursor:
            cursor.execute(" update DMY.IBNR_PARAMETRE ip set ip.ZONE_EUROPE = %s WHERE ip.BRANCHE = %s  ", [new_zone_europe,branche])
    if new_zone_amerique_asie != old_zone_amerique_asie :
        with connection.cursor() as cursor:
            cursor.execute(" update DMY.IBNR_PARAMETRE ip set ip.ZONE_AMERIQUE_ASIE = %s WHERE ip.BRANCHE = %s  ", [new_zone_amerique_asie,branche])
    request_set_sous_2 = where_clause_zone (new_zone_afrique , new_zone_amerique_asie, new_zone_europe )
    with connection.cursor() as cursor:
        #SET ALL TAUX TO 1 TO AVOID CERTAIN CASES WHERE THE TAUX WOULD NOT BE UPDATED 
        cursor.execute("  UPDATE DMY.IBNR_DETAIL id SET id.TAUX  = 1 WHERE id.BRANCHE = %s ",[branche])
        for ligne in liste :
            cursor.execute("  UPDATE DMY.IBNR_DETAIL id SET id.TAUX  = %s WHERE id.BRANCHE = %s AND id.UNDERWRITING_YEAR =%s "+ request_set_sous + request_set_sous_2,[ligne[0],branche,ligne[1]])
        cursor.execute("UPDATE DMY.IBNR_DETAIL idd SET idd.SAP_IBNR = idd.SAP * idd.TAUX ")
        cursor.execute("UPDATE DMY.IBNR_DETAIL idd SET idd.IBNR = idd.SAP_IBNR - idd.SAP")
    
    context = ibnr_display(request,branche)
    
    return render(request, 'main/templates/ibnr.html' ,context )

@login_required
@permission_required('cet.view_ibnr' ,raise_exception =True)
def ibnr_reinitialiser(request) :
    if request.method == 'GET':
        branche = request.GET.get('branche_hidden')
        
    with connection.cursor() as cursor:
            cursor.execute("UPDATE DMY.IBNR_DETAIL id SET id.TAUX = 1 ,  id.IBNR = 0 , id.SAP_IBNR =0 WHERE id.BRANCHE = %s ",[branche])

            cursor.execute("UPDATE DMY.IBNR_DETAIL idd SET idd.SAP_IBNR = idd.SAP * idd.TAUX ")
            cursor.execute("UPDATE DMY.IBNR_DETAIL idd SET idd.IBNR = idd.SAP_IBNR - idd.SAP")

    context = ibnr_display(request,branche)

    return render(request, 'main/templates/ibnr.html' ,context )

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.view_ibnr' ,raise_exception =True)
def resume_ibnr(request):
    totale_avant_ibnr = 0
    totale_ibnr = 0
    totale_apres_ibnr = 0
    resume_sap = []
    test =''
    condition = False
    message = ''
    with connection.cursor() as cursor:
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row =cursor.fetchone()
        CET_EN_COURS = row[0]
        cursor.execute("SELECT * FROM dmy.CET_PERIODE cp WHERE cp.NUM_CET = %s ",[CET_EN_COURS])
        row2 = cursor.fetchone()
        if row2 is  not None : 
            test = row2[0]
            if  test : 
                message = 'Le cet est insérer !!'
                condition = True
            else :
                message = 'Veuillez insrer le cet 1 !!' #USELESS DELETE IT 
        else :
            message = 'Veuillez insrer le cet 2 !!'
            condition = False
    if condition :
        with connection.cursor() as cursor:
            cursor.execute(""" 
                                SELECT 
                                    tt.branche ,
                                    tt.sap,
                                    tt.ibnr,
                                    tt.sap_ibnr,
                                    tt.portfolio,
                                    tt.zone
                                FROM 
                                (
                                SELECT 	id.BRANCHE ,
                                            sum(id.SAP) SAP ,
                                            sum(id.IBNR) IBNR ,
                                            sum(id.SAP_IBNR) SAP_IBNR ,
                                            DECODE( ip.TRAITE , 1 ,'Traite',0,' ')  || DECODE( ip.FAC , 1 ,' Fac',0,' ') AS PORTFOLIO ,
                                            decode(ip.ZONE_ALGERIE , 1 ,'Algerie ' ,0 ,'') ||
                                            decode(ip.ZONE_AFRIQUE , 1 ,'Afrique ' ,0 ,' ') ||
                                            decode(ip.ZONE_AMERIQUE_ASIE , 1 ,'Amerique Asie ' ,0 ,' ') ||
                                            decode(ip.ZONE_EUROPE , 1 ,'Europe ' ,0 ,' ')  AS ZONE
                                    FROM
                                        DMY.IBNR_DETAIL id
                                    JOIN DMY.IBNR_PARAMETRE ip ON ip.BRANCHE = id.BRANCHE 
                                    WHERE 
                                        id.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)
                                        --AND sum(id.SAP) != sum(id.SAP_IBNR)
                                    GROUP BY 
                                        id.BRANCHE,
                                        ip.TRAITE ,
                                        ip.fac,
                                        ip.ZONE_ALGERIE ,
                                        ip.ZONE_AFRIQUE ,
                                        ip.ZONE_AMERIQUE_ASIE ,
                                        ip.ZONE_EUROPE 
                                    ORDER BY 
                                        id.BRANCHE 
                                )tt
                                
                                WHERE tt.ibnr != 0  
                                 """  )
            page = cursor.fetchall()
            for row_num, columns in enumerate(page):
                liste =[]
                for col_num, cell_data in enumerate(columns):
                    #if not isinstance(cell_data,str) and (col_num ==1 or col_num ==2 or col_num ==3 ):
                    if col_num ==1 :
                        totale_avant_ibnr = totale_avant_ibnr +cell_data
                    if col_num ==2 :
                        totale_ibnr = totale_ibnr +cell_data
                    if col_num ==3 :
                        totale_apres_ibnr = totale_apres_ibnr +cell_data
                    
                    liste.append(cell_data)
                resume_sap.append(liste)
    context = {
        'resume_sap' : resume_sap,
        'message'  : message ,
        'condition' : condition,
        'totale_avant_ibnr' : totale_avant_ibnr ,
        'totale_ibnr' : totale_ibnr ,
        'totale_apres_ibnr' : totale_apres_ibnr

    }
    return render(request, 'main/templates/resume_ibnr.html' ,context )

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.view_ibnr' ,raise_exception =True)
def apercu_ibnr(request): 
    #GENERATES A PDF WITH THE IBNR 
    type_souscriptions = ['A','R','N']
    zones = ['1','2','3','4','*','?']
    branches =get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    year = ''
    registerFont(TTFont('Calibri', 'Calibri.ttf')) # Just some font imports
    registerFont(TTFont('Calibri-Bold', 'calibrib.ttf'))
    registerFont(TTFont('Arial', 'Arial.ttf')) 
    registerFont(TTFont('Georgia', 'Georgia.ttf')) 
    registerFont(TTFont('Verdana', 'Verdana.ttf')) 
    registerFont(TTFont('Tahoma', 'Tahoma.ttf'))

    #Initialiser les tables et les variables 
    with connection.cursor() as cursor:
        cursor.execute("""
                    INSERT INTO DMY.CET_PDF_TEMP cpt
                    SELECT 
                        rownum  AS id,
                        cc.NUM_CET ,
                        cc.SEQUENCE_NUMBER ,
                        cc.PORTFOLIO_TYPE ,
                        cc.TYPE_CONTRAT ,
                        cc.ZONE_CODE ,
                        cc.CODE_REGION ,
                        cc.UNDERWRITING_YEAR ,
                        cc.BRANCH_CODE ,
                        cc.BRANCHE ,
                        cc.SOUS_BRANCHE ,
                        cc.SUB_PROFIT_CENTRE_CODE ,
                        cc.TYPE_SOUSCRIPTION ,
                        cc.CEDANTE ,
                        nvl(cp2.PRIMES_ENCAISS,0),
                        nvl(cc2.CHARGES,0) ,
                        nvl(cc2.COURTAGE,0) ,
                        nvl(cp2.ENT_PRT_PRIME,0) ,
                        nvl(cp2.SOR_PRT_PRIME,0) ,
                        nvl(cc2.SINISTRE,0) ,
                        nvl(cp.PROV_SIN_OUV,0) ,
                        nvl(ci.PROV_SIN_CLO,0) ,-----MODIF ICI
                        nvl(cp.PROV_PRI_OUV,0) ,
                        nvl(cp.PROV_PRIM_CLO,0) ,
                        nvl(cee.PROV_EGAL_OUV,0) ,
                        nvl(cee.PROV_EQUI_OUV,0) ,
                        nvl(cee.PROV_EGAL_CLO,0) ,
                        nvl(cee.PROV_EQUI_CLO,0) 
                    FROM 
                        dmy.CET_CONTRAT cc 
                        LEFT JOIN dmy.CET_CHARGES cc2 ON cc2.id = cc.ID 
                        LEFT JOIN dmy.CET_PROV cp ON cp.id = cc.id 
                        LEFT JOIN DMY.CET_PRIM cp2 ON cp2.id = cc.id 
                        LEFT JOIN dmy.CET_IBNR ci ON ci.ID = cc.id
                        LEFT JOIN DMY.CET_EGAL_EQUI cee ON cee.ID = cc.id AND (SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '2EME SEMESTRE'
                    WHERE cc.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp) AND 
                        ( nvl(cp2.PRIMES_ENCAISS,0) <>0 OR 
                            nvl(cc2.CHARGES, 0) <> 0 
                            OR nvl(cc2.COURTAGE,0) <> 0 OR 
                            nvl(cp2.ENT_PRT_PRIME,0) <> 0 OR 
                            nvl(cp2.SOR_PRT_PRIME,0) <> 0 OR 
                            nvl(cc2.SINISTRE,0) <>0 OR 
                            nvl(cp.PROV_SIN_OUV,0) <>0 OR 
                            nvl(ci.PROV_SIN_CLO,0) <>0 OR 
                            nvl(cp.PROV_PRI_OUV,0) <>0 OR 
                            nvl(cp.PROV_PRIM_CLO,0) <>0 OR 
                            nvl(cee.PROV_EGAL_OUV,0) <>0 OR 
                            nvl(cee.PROV_EGAL_CLO,0) <>0 OR 
                            nvl(cee.PROV_EQUI_OUV,0) <>0 OR 
                            nvl(cee.PROV_EQUI_CLO,0) <>0 
                            )  
                        """)
        cursor.execute("""    UPDATE DMY.CET_PDF_TEMP cpt SET cpt.PROV_SIN_CLO = cpt.PROV_SIN_CLO * nvl (
																			(SELECT 
																				id.taux
																			FROM DMY.IBNR_DETAIL id
																			JOIN DOP.BRANCHES_CET bc ON bc.BRANCH_NAME = id.BRANCHE 
																			WHERE 
																				cpt.BRANCHE= bc.BRANCH_GROUP_CODE 
																				AND id.UNDERWRITING_YEAR = cpt.UNDERWRITING_YEAR 
																				AND cpt.PORTFOLIO_TYPE =id.PORTFOLIO_TYPE
																				AND cpt.ZONE_CODE = id.ZONE_CODE) ,
																				
																			nvl((SELECT 
																			id.taux
																			FROM DMY.IBNR_DETAIL id
																			JOIN DOP.BRANCHES_CET bc ON bc.BRANCH_NAME = id.BRANCHE 
																			WHERE 
																				cpt.BRANCHE= bc.BRANCH_GROUP_CODE 
																				AND id.UNDERWRITING_YEAR = 1111
																				AND cpt.PORTFOLIO_TYPE =id.PORTFOLIO_TYPE
																				AND cpt.ZONE_CODE = id.ZONE_CODE),1)
																		   )
                                WHERE cpt.TYPE_SOUSCRIPTION = 'A'""")
        cursor.execute("""
                        UPDATE DMY.CET_PDF_TEMP cpt SET cpt.PROV_SIN_CLO = cpt.PROV_SIN_CLO * nvl (
																			(SELECT 
																				id.taux
																			FROM DMY.IBNR_DETAIL id 
																			WHERE 
																				 id.UNDERWRITING_YEAR = 9999 
																				AND cpt.PORTFOLIO_TYPE =id.PORTFOLIO_TYPE
																				AND cpt.ZONE_CODE = id.ZONE_CODE ) , 1)
                        WHERE cpt.TYPE_SOUSCRIPTION = 'A' AND cpt.ZONE_CODE IN (2,3,4)   
                        """)
    #Lors du 1er trimestre pour la retro, affecter aux PROV_SIN_CLO les PROV_SIN_OUV
    # pour eviter d'avoir une perte trop importante dans le net     
    #
        cursor.execute("""
            UPDATE DMY.CET_PDF_TEMP tdf 
	        SET 
		        tdf.PROV_SIN_CLO = tdf.PROV_SIN_OUV 
		        WHERE tdf.TYPE_SOUSCRIPTION = 'R'
		        AND ( SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp) = '1ER TRIMESTRE'
             """)
        cursor.execute("delete from CET_PDF_FAST_V2")
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row1 =cursor.fetchone()
        numero_cet = row1[0]
        cursor.execute("SELECT scp.UNDERWRITING_YEAR FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        UNDERWRITING_YEAR = row2[0]
        year = str(UNDERWRITING_YEAR)
        cursor.execute("SELECT scp.EXERCICE FROM DMY.CET_PARAMETRES scp")
        row3 =cursor.fetchone()
        exercice = row3[0]
        cursor.callproc("DMY.CET_PDF_CALCULE2",[numero_cet,2021]) # Le deuxieme parametre n'est pas utiliser penser à le supprimer
        cursor.execute("SELECT  count(*)  FROM  (SELECT  DISTINCT spfv.TYPE_SOUSCRIPTION , SPFV .BRANCHE , SPFV .ZONE_CODE FROM DMY.CET_PDF_FAST_V2 spfv )")
        row = cursor.fetchone()
        nombre_pages = row[0]


    # Create a file-like buffer to receive PDF data.
    buffer = io.BytesIO()

    # Create the PDF object, using the buffer as its "file."

    now = datetime.now()
    dt_string = now.strftime("%d_%m_%Y %H-%M-%S")
    name_pdf = 'CET_PROVISOIRE_'+dt_string+'.pdf'
    p = canvas.Canvas("pdf/"+name_pdf)
    

    #Creating THE PAGE DE GARDE
    p.setPageSize(portrait(A4))
    p.setFillColorRGB(84/255,119/255,157/255)

    # THE RECTANGLE AT THE TOP OF THE PAGE
    p.rect(0,712,600,130, fill=1 ,stroke=False) 

    # THE RECTANGLE AT THE MIDDLE OF THE PAGE
    p.setFillColorRGB(156/255,158/255,159/255)
    p.rect(0,132,600,580, fill=1 ,stroke=False)
    
    #THE TEXTE AT THE TOP OF THE PAGE 
    p.setFillColorRGB(255/255,255/255,255/255)
    p.setFont("Helvetica-Bold", 20)
    p.drawString(30, 790, "COMPTE D'EXPLOITATION TECHNIQUE")
    p.setFont("Helvetica-Bold", 16)
    p.drawString(30, 770, "COMPAGNIE CENTRALE DE REASSURANCE" )
    p.drawString(30, 750, str(exercice) )
    #THE IMAGE AT AND THE SLOGAN AT THE BOTTOM OF THE PAGE 
    Image =ImageReader('img/logoShort.png')
    p.drawImage(Image,420,30, width=114,height=70,mask='auto')
    p.setFillColorRGB(84/255,119/255,157/255)
    p.setFont("Helvetica-Bold", 14)
    p.drawString(30, 50, "Serving your challenges, Supporting your activity" )

    #THE YEAR AT THE MIDDLE OF THE PAGE
    p.setFont("Helvetica", 210)
    p.drawString(90, 180, str(UNDERWRITING_YEAR)  )

    p.showPage()
    #THE SOMMAIRE 
    p.setFont("Helvetica", 25)
    p.setFillColorRGB(84/255,119/255,157/255)

    page_sommaire = 1 
    
    souscription = ' '
    for k1 in type_souscriptions :
        x=158
        y=700
        
        p.setFillColorRGB(84/255,119/255,157/255)
        p.setFont("Helvetica", 15)
        p.drawString(45, 770, "SOMMAIRE       "+str(exercice)+" "+str(UNDERWRITING_YEAR) )
        p.setFont("Helvetica", 10)
        p.drawString(x, y+30, decoderSouscriton(k1))
        y =y -20
        branches_deja_fait =[]
        for j1 in branches :
            for i1 in zones :
                condition1 = True
                condition2 = True
                p.setFillColorRGB(0/255,0/255,0/255)
                page = Pdf_fast_v2.objects.filter(type_souscription= k1).filter(branche=j1).filter(zone_code = i1)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :     
                    condition2= False
                if (condition1 == True) or (condition2 == True) : 
                    if k1 == 'A' and j1 not in branches_deja_fait :
                        branches_deja_fait.append(j1)
                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), 
                                                 ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                        
                        
                    elif k1 =='R' or k1 =='N' :

                        data = [[ ' '+decoderBranche(j1) ,str(page_sommaire) ]]
                        f = Table(data ,colWidths=[280,100],rowHeights=[40]) 
                        f.setStyle(TableStyle([('ALIGN',(1,0),(1,0),'RIGHT'), 
                                                ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                                                ('VALIGN',(0,0),(-1,-1),'MIDDLE'),
                                                 ('FONTSIZE', (0,0), (-1, -1), 9), ]))
                        if decoderBranche(j1) == 'FIRE' :
                            f.setStyle(TableStyle([('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        if decoderBranche(j1) == 'TOUTES BRANCHES' :
                            f.setStyle(TableStyle([('LINEBELOW', (0,0), (-1,-1), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),]))
                        f.wrapOn(p, 400, 400)
                        f.drawOn(p,x, y) 
                        y=y-25
                    page_sommaire = page_sommaire + 1 
        p.showPage()       

    #PRINT THE TABLES 
    p.setPageSize(landscape(A4))

    
    
    
    #Condition to check if a page is empty
    condition1 = True
    condition2 = True
    #table_pdf = Pdf_fast_v2.objects.all()
    page_en_cours = 1

    for k in type_souscriptions :
        for j in branches :
            for i in zones :

                #Condition to check if a page is empty
                condition1 = True
                condition2 = True

                page = Pdf_fast_v2.objects.filter(type_souscription= k).filter(branche=j).filter(zone_code = i)
                colonne1 = page.filter(portfolio_type ='1')
                colonne2 = page.filter(portfolio_type ='2')
                
                if colonne1.exists():
                    p1 = colonne1[0]
                else :
                    p1= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)   
                    condition1= False 
                if colonne2.exists():
                    p2 = colonne2[0]  
                else :
                    p2= Pdf_fast_v2(sinistre_1= 0 ,prov_sin_ouv_2=0,prov_sin_clo_3=0 ,SINISTRES_COMP_EXE_4=0,SINISTRES_PRIMES_ACQU_5 =0,les_charges_6=0,
                        commissions_primes_7=0,courtage_8=0,prov_egal_ouv_24=0,prov_equi_ouv_25=0,prov_egal_clo_26=0,prov_egal_clo_ouv_22=0,
                        prov_equi_clo_ouv_23=0,total_9=0,primes_encaiss_10=0,ent_prt_prime_11=0,sor_prt_prime_12=0,primes_nettes_13=0,
                        primes_nettes_ann_16=0,prov_pri_ouv_17=0,prov_prim_clo_18=0,primes_acquises_exe_19=0,BENEFICE_PERTE_20=0,rn_pra_21=0,prov_equi_clo_27=0)     
                    condition2= False 
                

            # check if page is empty
                if (condition1 == True) or (condition2 == True) : 

            #Formating data with thousands separator and eliminate the 0.00 and replace it with empty String
                    ligne1 = [   p1.sinistre_1 , p2.sinistre_1 , (p1.sinistre_1 + p2.sinistre_1) ]
                    ligne1formated = ['SINISTRES REGLES ET RACHAT']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne1]
                    ligne2 = [  p1.prov_sin_ouv_2,  p2.prov_sin_ouv_2, (p1.prov_sin_ouv_2+ p2.prov_sin_ouv_2) ]
                    ligne2formated = ['PROVISION SINISTRE OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne2]
                    ligne3 = [   p1.prov_sin_clo_3,  p2.prov_sin_clo_3 ,(p1.prov_sin_clo_3+ p2.prov_sin_clo_3) ]
                    ligne3formated = ['PROVISION SINISTRE CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne3]
                    ligne4 = [  p1.SINISTRES_COMP_EXE_4,  p2.SINISTRES_COMP_EXE_4 ,(p1.SINISTRES_COMP_EXE_4 +p2.SINISTRES_COMP_EXE_4)]
                    ligne4formated = ['SINISTRES DE COMPETENCE EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne4]
                    ligne6 =  [   p1.les_charges_6 ,  p2.les_charges_6 ,(p1.les_charges_6+p2.les_charges_6)]
                    ligne6formated = ['COMMISSIONS ET CHARGES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne6]
                    ligne8 = [   p1.courtage_8,  p2.courtage_8,(p1.courtage_8+p2.courtage_8)]
                    ligne8formated = ['COURTAGE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if '{:,.2f}'.format(elem) != '0.00' else '' for elem in ligne8]
                    ligne9 = [   p1.prov_egal_ouv_24,  p2.prov_egal_ouv_24, (p1.prov_egal_ouv_24+ p2.prov_egal_ouv_24)]
                    ligne9formated = ['PROVISIONS EGALISATION OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne9]
                    ligne10 = [   p1.prov_equi_ouv_25 ,  p2.prov_equi_ouv_25, (p1.prov_equi_ouv_25+ p2.prov_equi_ouv_25) ]
                    ligne10formated = ['PROVISIONS EQUILIBRAGE OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00'  else '' for elem in ligne10]
                    ligne11 = [  p1.prov_egal_clo_26 ,  p2.prov_egal_clo_26,(p1.prov_egal_clo_26 +p2.prov_egal_clo_26) ]
                    ligne11formated = ['PROVISIONS EGALISATION CLOTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne11]
                    ligne12 =[  p1.prov_equi_clo_27,  p2.prov_equi_clo_27,(p1.prov_equi_clo_27+p2.prov_equi_clo_27)]
                    ligne12formated = ['PROVISIONS EQUILIBRAGE CLOTURE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne12]
                    ligne13 = [  p1.prov_egal_clo_ouv_22 ,  p2.prov_egal_clo_ouv_22,(p1.prov_egal_clo_ouv_22+p2.prov_egal_clo_ouv_22)]
                    ligne13formated = ['PROVISIONS EGALISATION CLOTURE-OUVERTURE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne13]
                    ligne14 = [   p1.prov_equi_clo_ouv_23 ,  p2.prov_equi_clo_ouv_23, (p1.prov_equi_clo_ouv_23+p2.prov_equi_clo_ouv_23)]
                    ligne14formated = ['PROVISIONS EQUILIBRAGE CLOTURE-OUVERTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne14]
                    ligne15 = [   p1.total_9 ,  p2.total_9 ,(p1.total_9+p2.total_9)]
                    ligne15formated = ['TOTAL']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne15]
                    ligne16 = [  p1.primes_encaiss_10 ,  p2.primes_encaiss_10,(p1.primes_encaiss_10+p2.primes_encaiss_10)]
                    ligne16formated = ['PRIMES EMISES'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne16]
                    ligne17 = [  p1.ent_prt_prime_11, p2.ent_prt_prime_11,(p1.ent_prt_prime_11 + p2.ent_prt_prime_11)]
                    ligne17formated = ['ENTREES PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne17]
                    ligne18 = [  p1.sor_prt_prime_12,  p2.sor_prt_prime_12,(p1.sor_prt_prime_12+p2.sor_prt_prime_12)]
                    ligne18formated = ['SORTIE PORTEFEUILLE PRIME']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne18]
                    ligne19 = [  p1.primes_nettes_13 ,  p2.primes_nettes_13,(p1.primes_nettes_13+p2.primes_nettes_13)]
                    ligne19formated = ['PRIMES NETTES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne19]
                    ligne20 = [  p1.primes_nettes_ann_16 ,   p2.primes_nettes_ann_16 ,(p1.primes_nettes_ann_16+p2.primes_nettes_ann_16)]
                    ligne20formated = ['PRIMES NETTES ANNUELLES']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne20]
                    ligne21 = [  p1.prov_pri_ouv_17,   p2.prov_pri_ouv_17,(p1.prov_pri_ouv_17+p2.prov_pri_ouv_17)]
                    ligne21formated = ['PROVISION PRIME OUVERTURE']+ [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne21]
                    ligne22 = [  p1.prov_prim_clo_18,  p2.prov_prim_clo_18,(p1.prov_prim_clo_18+p2.prov_prim_clo_18)]
                    ligne22formated = ['PROVISION PRIME CLOTURE'] + [ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne22]
                    ligne23 = [  p1.primes_acquises_exe_19 ,  p2.primes_acquises_exe_19,(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19)]
                    ligne23formated = ['PRIMES ACQUISES EXERCICE']+[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne23]
                    ligne24 = [  p1.BENEFICE_PERTE_20 ,  p2.BENEFICE_PERTE_20,(p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)]
                    ligne24formated = ['BENEFICE/PERTE'] +[ '{:,.2f}'.format(elem).replace(',', ' ')  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne24]
                    

        # Format data to eliminate the 0.00 and the -0.00 and replace it with empty String
                    ligne1SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne1formated]
                    ligne2SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne2formated]
                    ligne3SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne3formated]
                    ligne4SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne4formated]
                    ligne6SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne6formated]
                    ligne8SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne8formated]
                    ligne9SuperFormated =  [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne9formated]
                    ligne10SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne10formated]
                    ligne11SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne11formated]
                    ligne12SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne12formated]
                    ligne13SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne13formated]
                    ligne14SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne14formated]
                    ligne15SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne15formated]
                    ligne16SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne16formated]
                    ligne17SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne17formated]
                    ligne18SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne18formated]
                    ligne19SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne19formated]
                    ligne20SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne20formated]
                    ligne21SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne21formated]
                    ligne22SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne22formated]
                    ligne23SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne23formated]
                    ligne24SuperFormated = [  '' if elem == '0.00' or elem == '-0.00' else elem    for elem in ligne24formated]


        #Reset values of totals
                    total_5 = 0
                    total_21 = 0
                    total_7 = 0
        # SPECIAL CALCULS WHITH DIVISIONS THE 5 7 AND 21 
                    if ((p1.primes_encaiss_10+p2.primes_encaiss_10) !=0 ) : 
                        total_7 = abs (100*(p1.les_charges_6+p2.les_charges_6)/(p1.primes_encaiss_10+p2.primes_encaiss_10))
                    if ( (p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) !=0 ) :
                        total_21 = abs ( 100*( (p1.BENEFICE_PERTE_20+p2.BENEFICE_PERTE_20)/(p1.primes_acquises_exe_19+p2.primes_acquises_exe_19) ) )
                    if ( ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) ) != 0  ) :
                        total_5 = abs ( 100*( (p1.sinistre_1+p2.sinistre_1) -(p1.prov_sin_ouv_2+p2.prov_sin_ouv_2)+(p1.prov_sin_clo_3+p2.prov_sin_clo_3) )/ ( (p1.primes_nettes_13+p2.primes_nettes_13) + (p1.prov_pri_ouv_17+p2.prov_pri_ouv_17) - (p1.prov_prim_clo_18+p2.prov_prim_clo_18) )    )
        # Formating the special lines            
                    
                    ligne5  =  [p1.SINISTRES_PRIMES_ACQU_5 ,  p2.SINISTRES_PRIMES_ACQU_5 ,total_5]
                    ligne5formated = ['SINISTRES/PRIMES ACQUISES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne5]  
                    ligne5SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne5formated]
                    
                    ligne7 = [  p1.commissions_primes_7,  p2.commissions_primes_7,total_7]
                    ligne7formated = ['COMMISSIONS/PRIMES  %']+ [ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne7]
                    ligne7SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne7formated]

                    ligne25 = [  p1.rn_pra_21,  p2.rn_pra_21,total_21]
                    ligne25formated = ['RN/PRA  %']+[ '{:,.2f}'.format(elem)  if ' {:,.2f}'.format(elem) != '0.00' else '' for elem in ligne25]
                    ligne25SuperFormated =  [  elem if elem != '0.00' else ''    for elem in ligne25formated]

                    data = [
                        ['BRANCHE '+decoderBranche(j), 'TRAITES', 'FACULTATIVES', 'TOTAL'],
                        ligne1SuperFormated,
                        ligne2SuperFormated,
                        ligne3SuperFormated,
                        ligne4SuperFormated,
                        ligne5SuperFormated,
                        ligne6SuperFormated,
                        ligne7SuperFormated,
                        ligne8SuperFormated,
                        ligne9SuperFormated,
                        ligne10SuperFormated,
                        ligne11SuperFormated,
                        ligne12SuperFormated,        
                        ligne13SuperFormated,
                        ligne14SuperFormated,
                        ligne15SuperFormated,
                        ligne16SuperFormated,
                        ligne17SuperFormated,        
                        ligne18SuperFormated,
                        ligne19SuperFormated,
                        ligne20SuperFormated,
                        ligne21SuperFormated,
                        ligne22SuperFormated,
                        ligne23SuperFormated,
                        ligne24SuperFormated,
                        ligne25SuperFormated]
                        
                    width = 400
                    height = 100
                    
        #DEFINE THE STYLING OF THE DATA TABLE

                    p.setFont('Times-Roman', 10)
                    f = Table(data ,colWidths=[252,140,140,140], 
                                    rowHeights=[18,25,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15,15])
                    f.setStyle(TableStyle([('ALIGN',(1,1),(-2,-2),'RIGHT'),
                        ('ALIGN', (0,0), (0,25), 'LEFT'),
                        ('ALIGN', (1,0), (-1,-1), 'RIGHT'),
                        ('LINEABOVE', (0,0), (-1,0), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,0), (-1,0), 1.4, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,1), (-1,24), 0.7, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('LINEBELOW', (0,25), (-1,25), 1.6, colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('VALIGN',(0,0),(3,0),'MIDDLE'),
                        ('VALIGN',(0,2),(-1,-1),'MIDDLE'),
                        ('BACKGROUND',(3,0),(3,25),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('BACKGROUND',(0,15),(3,15),colors.Color(red=(231/255),green=(231/255),blue=(232/255))),
                        ('TEXTCOLOR',(0,0),(3,0),colors.Color(red=(84/255),green=(119/255),blue=(157/255))),
                        ('TEXTCOLOR',(0,1),(-1,-1),colors.Color(red=(0/255),green=(0/255),blue=(0/255))),
                        ('FONTNAME', (0,0), (-1,-1), 'Verdana'),
                        ('FONTSIZE', (1,1), (-1, -1), 10), 
                        ]))
                    f.wrapOn(p, width, height)
                    f.drawOn(p,76, 40) 

        #PRINT THE SOUSCRIPTION AND ZONE
                    p.setFont("Helvetica-Bold", 13)
                    p.setFillColorRGB(84/255,119/255,157/255) #choose your font colour
                    zone_texte = ''
                    if k == 'A' : 
                        zone_texte = decoderZone(i)
                    
                    p.drawString(82, 480, decoderSouscriton(k)+' '+ zone_texte)

                #PRINT THE OTHER LINES 
                    p.setFont("Helvetica-Bold", 17)
                    p.drawString(82, 550, "COMPTE D'EXPLOITATION TECHNIQUE" )
                    p.setFont("Helvetica", 11)
                    p.drawString(82, 530, "PAR BRANCHES ET REGIONS EN DINARS ALGERIENS" )
                    p.setFont("Helvetica", 9)

                #PRINT THE IMAGE LOGO and OTHER STUFF
                    p.setFillColorRGB(0/255,0/255,0/255)
                    #p.drawString(82, 450, "EN MILLION DE DINARS")
                    p.drawString(688, 450, "ANNEE "+year)
                    Image =ImageReader('img/logo02.png')
                    p.drawImage(Image,452,525, width=297,height=52,mask='auto')   

                # PRINT THE PAGE NUMBER AND THE DATE
                    p.drawString(688, 23,"PAGE "+str(page_en_cours)+"/"+str(nombre_pages))
                    today = date.today()
                    d1 = today.strftime("%d/%m/%Y %H-%M-%S")
                    p.drawString(82, 23,dt_string.replace('_','/'))
                    page_en_cours = page_en_cours+1

                #GO TO THE NEXT PAGE

                    p.showPage()
    # Close the PDF object cleanly, and we're done.

    p.save()

    # FileResponse sets the Content-Disposition header so that browsers
    # present the option to save the file.

    buffer.seek(0)
    # GET THE STATUS OF RMS SYSTEM
    with connection.cursor() as cursor:
        cursor.execute(" SELECT scp.IS_RMS_ACTIVE FROM dmy.CET_PARAMETRES scp ")
        row5 = cursor.fetchone()
        rms_active = row5[0]

    context = {
        'name_pdf': name_pdf ,
        'rms_active' : rms_active ,
        'origine' : 'ibnr'
    }
    #return FileResponse(buffer, as_attachment=True, filename='hello.pdf')
    
    return render(request, 'main/templates/pdf.html' , context )

@login_required
@permission_required('cet.view_ibnr' ,raise_exception =True)
def valider_ibnr(request) :
    #Retrieve data 
    name_pdf = 'teste.pdf'
    if request.method == 'POST':
        name_pdf = request.POST.get('name_pdf')
    
    #VALIDATE IBNR
    with connection.cursor() as cursor:
        cursor.callproc("INSERER_IBNR")

    context = {
        'validation_ibnr': 1 ,
        'message'  : 'Validation des IBNR réussie' ,
        'name_pdf': name_pdf
    }

    return render(request, 'main/templates/pdf.html',context)

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
@permission_required('cet.view_ibnr' ,raise_exception =True)
def view_matrice_dev(request):
    first_view = False

    selected_branche = '?'
    select= ''
    if request.method == 'GET':
        type_donnee = request.GET.get('type_donnee')
        branche = request.GET.get('branche')
        zone = request.GET.get('zone')
        portfolio = request.GET.get('portfolio')
        methode = request.GET.get('methode')
        periode = request.GET.get('periode')
 
    #CHECK IF IT IS THE FIRST VIEW OF THE PAGE 
    if  branche  is None  and  zone  is None and portfolio  is None :
        first_view = True 
    #NORMALISER LES DONNEE : ne pas les laisser en noneType ou NONE
    if  periode is None :
        periode = '2eme'
    if  branche  is None :
        branche = '?'
    if  zone  is None :
        zone = '?'
    if  portfolio  is None :
        portfolio = '?'
    if  methode  is None :
        methode = 'cl'
    if type_donnee  is None :
        selected_type_donne = 'sinistre'
        # par default on prend les sinistres 
        select =',round (sum(x.SINISTRE),2) AS SINISTRE '
    else :
        if type_donnee == 'prime' :
            select =',round (sum(x.prime ),2) AS PRIME '
            selected_type_donne= 'prime'
        if type_donnee == 'sinistre' :
            select =',round (sum(x.SINISTRE),2) AS SINISTRE '
            selected_type_donne= 'sinistre'
        if type_donnee == 'sap' :
            select =',round (sum(x.sap),2) AS sap '
            selected_type_donne= 'sap'
    if  periode == '1er' : 
        vue = 'DMY.IBNR_MATRICE_DEV_1_SEM_M'
    if  periode =='2eme' : 
        vue = 'DMY.IBNR_MATRICE_DEV_2_SEM_M'
    # PRISE EN COMPTE DE LA BRANCHE  de la zone et du portfolio   
    where =  where_clause(branche , zone , portfolio)

    if not first_view : 
        liste_dev = []
        #GET THE DATA FROM DATABASE 
        with connection.cursor() as cursor :
            cursor.execute(" SELECT x.ANNEE ,x.UNDERWRITING_YEAR "+select + " FROM "+ vue +" x "+ where  +" GROUP BY x.ANNEE ,x.UNDERWRITING_YEAR ORDER BY x.ANNEE ,x.UNDERWRITING_YEAR ")
            page = cursor.fetchall()
            for row_num, columns in enumerate(page):
                liste1 =[]
                for col_num, cell_data in enumerate(columns):
                    liste1.append(cell_data)
                liste_dev.append(liste1)

        if (liste_dev  and len(liste_dev) > 2) and not first_view: # 2 IS ARBITRARY IT'S JUST TO IGNORE CASES WHERE THE SELECT RETURNS 1 OR 2 ROWS 
            #METTRE LES DONNEES DANS LE DATA FRAME PANDAS 
            df = pd.DataFrame(liste_dev)
            #RENOMER LES COLONNES
            df.columns = ["annee" , "underwriting_year","sinistre"]
            #CONVERTIRE LE TYPE DE DONNEE EN FLOAT64
            df["sinistre"] = df["sinistre"].astype('float64')
            #GENERER LA MATRICE TRIANGULAIRE AVANT CUMUL
            prism = cl.Triangle(data=df, origin="underwriting_year", development="annee", columns="sinistre" )
            #LA MATRICE APRES CUMUL UNIQUEMENT POUR PRIME ET SINISTRE
            if type_donnee != 'sap' :
                prism = prism.incr_to_cum()
            #APPLICATION DE CHAIN LADDER
            if methode == 'cl' :
                genins_model = cl.Chainladder().fit(prism)

            if methode == 'mackcl' :
                genins_model = cl.MackChainladder().fit(prism)

            
            mat_chainladder = genins_model.full_triangle_

            #LA COLONNE QUI DONNE LES IBNR ET SA CONVERSION EN LISTE PYTHON
            df3 = genins_model.ibnr_.to_frame()
            df3 = df3.fillna(0)
            liste_ibnr = df3.values.tolist()

            #CONVERTIRE L'IBJET CL EN OBJET LISTE PYHTON
            df = prism.to_frame()
            df = df.fillna(0)
            liste = df.values.tolist()

            liste_corrige= []
            annee = 2009
            for x in liste : 
                ll = []
                ll.append(annee)
                for y in x :
                    ll.append(y)
                annee = annee +1 
                liste_corrige.append(ll)

            x=0
            annee_dev =[]
            while x <= len(liste_corrige) :
                if x == 0 :
                    annee_dev.append('ANNEE')
                else :
                    annee_dev.append(x)
                x =x +1
            if type_donnee != 'sap' : 
                annee_dev.append("IBNR")
            # CONVERTIRE LA MATRICE CHAIN LADDER EN LISTE PYHTON 
            df2 = mat_chainladder.to_frame()
            df2 = df2.fillna(0)
            liste_chain_ladder = df2.values.tolist()

            liste_corrige_chain_ladder= []
            annee = 2009
            i=0
            for x in liste_chain_ladder : 
                x.pop()
                x.pop()
                ll = []
                ll.append(annee)
                for y in x :
                    ll.append(y)
                annee = annee +1
                if type_donnee != 'sap' : 
                    ll.append(liste_ibnr[i][0])
                i = i+1
                liste_corrige_chain_ladder.append(ll)

            dataDictionary = {
                'periode' : periode ,
                'branche' : branche ,
                'zone' : zone ,
                'portfolio' : portfolio ,
                'selected_type_donne' : selected_type_donne ,
                'methode' : methode
            }
            # dump data
            dataJSON = json.dumps(dataDictionary)
            context = {
                'data' : dataJSON ,
                'message' : "message de la vue" ,
                'liste' : liste_corrige ,
                'annee_dev' : annee_dev ,
                'matrice_remplie' : liste_corrige_chain_ladder ,
                'selected_type_donne' : selected_type_donne ,
            }
        else : 
            dataDictionary = {
                'periode' : periode ,
                'branche' : branche ,
                'zone' : zone ,
                'portfolio' : portfolio ,
                'selected_type_donne' : selected_type_donne ,
                'methode' : methode
            }
            # dump data
            dataJSON = json.dumps(dataDictionary)
            context = {
                'data' : dataJSON ,
                'vide' : '1'
            }
    else : 
        dataDictionary = {
                'periode' : periode ,
                'branche' : branche ,
                'zone' : zone ,
                'portfolio' : portfolio ,
                'selected_type_donne' : selected_type_donne ,
                'methode' : methode
            }
        # dump data
        dataJSON = json.dumps(dataDictionary)
        context = {
            'data' : dataJSON ,
            'vide' : '1'
        }

    return render(request, 'main/templates/matrice_dev.html',context)

@login_required
@permission_required('cet.view_ibnr' ,raise_exception =True)
def excel_matrice_ibnr(request) : 
    if request.method == 'GET':
        type_donnee = request.GET.get('type_donnee')
        branche = request.GET.get('branche')
        zone = request.GET.get('zone')
        portfolio = request.GET.get('portfolio')
        type_matrice = request.GET.get('type_matrice')
        periode = request.GET.get('periode')
    #NORMALISER LES DONNEE : ne pas les laisser en noneType ou NONE

    if  periode is None :
        periode = '2eme'
    if  branche  is None :
        branche = '?'
    if  zone  is None :
        zone = '?'
    if  portfolio  is None :
        portfolio = '?'
    if type_donnee  is None :
        # par default on prend les sinistres 
        select =',round (sum(x.SINISTRE),2) AS SINISTRE '
    else :
        if type_donnee == 'prime' :
            select =',round (sum(x.prime ),2) AS PRIME '
            selected_type_donne= 'prime'
        if type_donnee == 'sinistre' :
            select =',round (sum(x.SINISTRE),2) AS SINISTRE '
        if type_donnee == 'sap' :
            select =',round (sum(x.sap),2) AS sap '
    if  periode == '1er' : 
        vue = 'DMY.IBNR_MATRICE_DEV_1_SEM_M'
    if  periode =='2eme' : 
        vue = 'DMY.IBNR_MATRICE_DEV_2_SEM_M'

    # PRISE EN COMPTE DE LA BRANCHE  de la zone et du portfolio   
    where =  where_clause(branche , zone , portfolio)
    #GET THE DATA FROM DATABASE 
    liste_dev = []
    with connection.cursor() as cursor :
        cursor.execute(" SELECT x.ANNEE ,x.UNDERWRITING_YEAR "+select + " FROM "+ vue +" x "+ where  +" GROUP BY x.ANNEE ,x.UNDERWRITING_YEAR ORDER BY x.ANNEE ,x.UNDERWRITING_YEAR ")
        
        page = cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                liste1.append(cell_data)
            liste_dev.append(liste1)
    #METTRE LES DONNEES DANS LE DATA FRAME PANDAS 
    df = pd.DataFrame(liste_dev)
    #RENOMER LES COLONNES
    df.columns = ["annee" , "underwriting_year","sinistre"]
    #CONVERTIRE LE TYPE DE DONNEE EN FLOAT64
    df["sinistre"] = df["sinistre"].astype('float64')
    #GENERER LA MATRICE TRIANGULAIRE AVANT CUMUL
    prism = cl.Triangle(data=df, origin="underwriting_year", development="annee", columns="sinistre" )
    ##sample_weight = prism.latest_diagonal*0+40_000
    #LA MATRICE APRES CUMUL UNIQUEMENT POUR PRIME ET SINISTRE
    if type_donnee != 'sap' :
        prism = prism.incr_to_cum()
    loop = ['triangulaire','complete']
    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()

    workbook = xlsxwriter.Workbook(output)
    
    for x in loop :   
        worksheet = workbook.add_worksheet(x)
        if x == 'triangulaire' :
            #CONVERTIRE L'IBJET CL EN OBJET LISTE PYHTON
            df = prism.to_frame()
            df = df.fillna(0)
            matrice_triangulaire_temp = df.values.tolist()
            

        if x == 'complete' :
            #CONVERTIRE L'IBJET CL EN OBJET LISTE PYHTON
            #APPLICATION DE CHAIN LADDER
            genins_model = cl.Chainladder().fit(prism)
            mat_chainladder = genins_model.full_triangle_
            df2 = mat_chainladder.to_frame()
            df2 = df2.fillna(0)

            #LA COLONNE QUI DONNE LES IBNR ET SA CONVERSION EN LISTE PYTHON
            df3 = genins_model.ibnr_.to_frame()
            df3 = df3.fillna(0)
            liste_ibnr = df3.values.tolist()
        
            matrice_triangulaire_temp = df2.values.tolist()
            mat_corr =[]
            i = 0 
            for x in matrice_triangulaire_temp : 
                x.pop()
                x.pop()
                ll= []
                for y in x :
                    ll.append(y)
                if type_donnee != 'sap' :
                    ll.append(liste_ibnr[i][0])
                i = i+1
                mat_corr.append(ll)
            matrice_triangulaire_temp = mat_corr

        #EXCEL GENARATION BEGINS HERE
        matrice_triangulaire= []# not realy a triangulaire matrice
        annee = 2009
        i=0
        for x in matrice_triangulaire_temp : 
            ll = []
            ll.append(annee)
            for y in x :
                ll.append(y)
            annee = annee +1 
            i = i+1
            matrice_triangulaire.append(ll)
        entete =[]
        x=0
        while x <= len(matrice_triangulaire) :
            if x == 0 :
                entete.append('ANNEE')
            else :
                entete.append(x)
            x =x +1

        i= 0
        for row_num, columns in enumerate(matrice_triangulaire):
            i = i+1 
        nb_lines = i 

        # Setup formats
        data_format = workbook.add_format({'num_format': 43 }) #'#,##0.00'
        number_format = workbook.add_format({'num_format': '#,##0'})
        exch_format = workbook.add_format({'num_format': '#,##0.00000'})
        year_format = workbook.add_format({'num_format': '####'})
        booked_format = workbook.add_format({'num_format': '####'})
        date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
        # Write the data and format it
        for row_num, columns in enumerate(matrice_triangulaire):
            for col_num, cell_data in enumerate(columns):
                if col_num > 0 :
                    worksheet.write(row_num+1, col_num, cell_data , data_format)
                else :
                    worksheet.write(row_num+1, col_num, cell_data)

        #Get the number of colums 
        nb_columns = len(entete)
    
        #Get the fields name 
        i=0
        fields=[]
        
        while i < len(entete):
            fields.append({'header': str(entete[i])})     
            i += 1

        #Write the table and apply some styling
        worksheet.add_table(0,0,nb_lines,nb_columns-1, {'style': 'Table Style Light 9', 
                                                    #'banded_rows': False ,
                                                    'banded_columns': True ,
                                                    'columns' : fields })

        # Resize the columns
        worksheet.set_column(0,nb_columns, 20)  # Columns F-H width set to 30.

    # Close the workbook before sending the data.
    workbook.close()

    # Rewind the buffer.
    output.seek(0)

    # Set up the Http response.
    filename = 'Matrice_Developpement.xlsx'
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response 

@login_required
@permission_required('cet.view_ibnr' ,raise_exception =True)
def excel_bloc_matrice_ibnr(request) :
    if request.method == 'GET':
        type_donnee = request.GET.get('type_donnee')
        branche = request.GET.get('branche')
        zone = request.GET.get('zone')
        portfolio = request.GET.get('portfolio')
        type_matrice = request.GET.get('type_matrice')
        periode = request.GET.get('periode')
    #type_matrice = 'triangulaire'
    #NORMALISER LES DONNEE : ne pas les laisser en noneType ou NONE

    branches = get_branches_cet('code')#['A','B','C','D','E','F','G','H','I','J','K','L','M','N','O','P','Q','R','S','T','U','V','W','X','?']
    # Create an in-memory output file for the new workbook.
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)

    loop = ['triangulaire','complete']
    for sub_loop in loop: 
        worksheet = workbook.add_worksheet(sub_loop)
        det = 0 
        for aa in branches : 
            branche = aa
            if  periode is None :
                periode = '2eme'
            if  zone  is None :
                zone = '?'
            if  portfolio  is None :
                portfolio = '?'
            if type_donnee  is None :
                # par default on prend les sinistres 
                select =',round (sum(x.SINISTRE),2) AS SINISTRE '
            else :
                if type_donnee == 'prime' :
                    select =',round (sum(x.prime ),2) AS PRIME '
                    selected_type_donne= 'prime'
                if type_donnee == 'sinistre' :
                    select =',round (sum(x.SINISTRE),2) AS SINISTRE '
                if type_donnee == 'sap' :
                    select =',round (sum(x.sap),2) AS sap '
            if  periode == '1er' : 
                vue = 'DMY.IBNR_MATRICE_DEV_1_SEM_M'
            if  periode =='2eme' : 
                vue = 'DMY.IBNR_MATRICE_DEV_2_SEM_M'

            # PRISE EN COMPTE DE LA BRANCHE  de la zone et du portfolio   
            where =  where_clause(branche , zone , portfolio)

            #GET THE DATA FROM DATABASE 
            liste_dev = []
            with connection.cursor() as cursor :
                cursor.execute(" SELECT x.ANNEE ,x.UNDERWRITING_YEAR "+select + " FROM " + vue +" x "+ where  +" GROUP BY x.ANNEE ,x.UNDERWRITING_YEAR ORDER BY x.ANNEE ,x.UNDERWRITING_YEAR ")
                page = cursor.fetchall()
                for row_num, columns in enumerate(page):
                    liste1 =[]
                    for col_num, cell_data in enumerate(columns):
                        liste1.append(cell_data)
                    liste_dev.append(liste1)

            if (liste_dev  and len(liste_dev) > 2) : 
                #METTRE LES DONNEES DANS LE DATA FRAME PANDAS 
                df = pd.DataFrame(liste_dev)
                #RENOMER LES COLONNES
                df.columns = ["annee" , "underwriting_year","sinistre"]
                #CONVERTIRE LE TYPE DE DONNEE EN FLOAT64
                df["sinistre"] = df["sinistre"].astype('float64')
                #GENERER LA MATRICE TRIANGULAIRE AVANT CUMUL
                prism = cl.Triangle(data=df, origin="underwriting_year", development="annee", columns="sinistre" )
                ##sample_weight = prism.latest_diagonal*0+40_000
                #LA MATRICE APRES CUMUL UNIQUEMENT POUR PRIME ET SINISTRE
                if type_donnee != 'sap' :
                    prism = prism.incr_to_cum()
                if sub_loop == 'triangulaire' :
                    #CONVERTIRE L'IBJET CL EN OBJET LISTE PYHTON
                    df = prism.to_frame()
                    df = df.fillna(0)
                    matrice_triangulaire_temp = df.values.tolist()

                if sub_loop == 'complete' :
                    #CONVERTIRE L'IBJET CL EN OBJET LISTE PYHTON
                    #APPLICATION DE CHAIN LADDER
                    genins_model = cl.Chainladder().fit(prism)
                    mat_chainladder = genins_model.full_triangle_
                    df2 = mat_chainladder.to_frame()
                    df2 = df2.fillna(0)

                    #LA COLONNE QUI DONNE LES IBNR ET SA CONVERSION EN LISTE PYTHON
                    df3 = genins_model.ibnr_.to_frame()
                    df3 = df3.fillna(0)
                    liste_ibnr = df3.values.tolist()
                
                    matrice_triangulaire_temp = df2.values.tolist()
                    mat_corr =[]
                    i = 0 
                    for x in matrice_triangulaire_temp : 
                        x.pop()
                        x.pop()
                        ll= []
                        for y in x :
                            ll.append(y)
                        if type_donnee != 'sap' :
                            ll.append(liste_ibnr[i][0])
                        i = i+1
                        mat_corr.append(ll)
                    matrice_triangulaire_temp = mat_corr
            
                #EXCEL GENARATION BEGINS HERE

                matrice_triangulaire= []# not realy a triangulaire matrice
                annee = 2009
                i=0
                for x in matrice_triangulaire_temp : 
                    ll = []
                    ll.append(annee)
                    for y in x :
                        ll.append(y)
                    annee = annee +1 
                    i = i+1
                    matrice_triangulaire.append(ll)
                entete =[]
                x=0
                while x <= len(matrice_triangulaire) :
                    if x == 0 :
                        entete.append('ANNEE')
                    else :
                        entete.append(x)
                    x =x +1

                i= 0
                for row_num, columns in enumerate(matrice_triangulaire):
                    i = i+1 
                nb_lines = i 

                
            
                
                worksheet.write( det , 0, decoderBranche(aa))
                # Setup formats
                data_format = workbook.add_format({'num_format': 43 }) #'#,##0.00'
                number_format = workbook.add_format({'num_format': '#,##0'})
                exch_format = workbook.add_format({'num_format': '#,##0.00000'})
                year_format = workbook.add_format({'num_format': '####'})
                booked_format = workbook.add_format({'num_format': '####'})
                date_format = workbook.add_format({'num_format': 'dd/mm/yyyy'})
                # Write the data and format it
                for row_num, columns in enumerate([entete]+ matrice_triangulaire):
                    for col_num, cell_data in enumerate(columns):
                        if ( col_num > 0 ) and (row_num > 0):
                            worksheet.write(row_num + 2 + det , col_num, cell_data , data_format)
                        else :
                            worksheet.write(row_num + 2 + det , col_num, cell_data)

                #Get the number of colums 
                nb_columns = len(entete)
            
                #Get the fields name 
                i=0
                fields=[]
                while i < len(entete):
                    fields.append({'header': str(entete[i])})     
                    i += 1

                #Write the table and apply some styling
                """worksheet.add_table( det,0,nb_lines,nb_columns-1, {'style': 'Table Style Light 9', 
                                                            #'banded_rows': False ,
                                                            'banded_columns': True ,
                                                            'columns' : fields })"""

                # Resize the columns
                worksheet.set_column(0,nb_columns, 20)  # Columns F-H width set to 30.

                det = det  +18
    # Close the workbook before sending the data.
    workbook.close()

    # Rewind the buffer.
    output.seek(0)

    # Set up the Http response.
    filename = 'Matrice_Developpement.xlsx'
    
    response = HttpResponse(
        output,
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename=%s' % filename

    return response 

@login_required
def view_changement_mdp(request) :
    return render(request, 'main/templates/securite.html')

@login_required
def success_change_password(request) :

    my_group = Group.objects.get(name='DONT_NEED_PASSWORD_CHANGE')
    my_group.user_set.add(request.user)
    return render(request, 'main/templates/password_change_done.html')

@login_required
@permission_required('cet.need_ch_pass' , login_url='/cet/view_changement_mdp')
def etatsexcelcna(request):
    liste_cet = []
    liste_directions = []
    row = []
    with connection.cursor() as cursor:
        #Get the info about CET
        cursor.execute("SELECT lc.ANNEE ,  lc.ID  FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC ")
        row = [(row1[0],row1[1]) for row1 in cursor.fetchall()]
        cursor.execute("SELECT scp.DATE_DEBUT_EXERCICE FROM DMY.CET_PARAMETRES scp ")
        row2 =cursor.fetchone()
        DATE_DEBUT_EXERCICE = row2[0]
        cursor.execute("SELECT * FROM DMY.LISTE_CET lc ORDER BY lc.ANNEE ASC")
        page= cursor.fetchall()
        for row_num, columns in enumerate(page):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                if col_num > 0 :
                    liste1.append(str(cell_data))
            liste_cet.append(liste1)
    liste_directions = get_directions()
    date_formated = str (DATE_DEBUT_EXERCICE.strftime('%Y-%m-%d') )
    dataDictionary = {
        'liste_cet' : liste_cet ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)
    liste_branches = get_branches_cet("excel")
    context = {
        'data' : dataJSON ,
        'list_cet' : row ,
        
         }
    return render(request, 'main/templates/etat_excel_cna.html',context)

@login_required
def tableaux_cna(request) :
    #time.sleep(5)
    if request.method == 'GET':
        annee = request.GET.get('annee')
        trim = request.GET.get('trim')
        type_data = request.GET.get('type')
    liste_inter= []
    liste_nat=[]
    view_int = '' 
    view_nat = ""
    with connection.cursor() as cursor :
        request1 = 'SELECT lc."'+trim+'" FROM DMY.LISTE_CET lc WHERE lc.ANNEE = %s'
        cursor.execute(request1,[annee])
        row23 =cursor.fetchone()
        num_cet = row23[0]
        #INSERT THE VARAIBLES INTO THE TEMPORARY TABLE
        cursor.execute("INSERT INTO DMY.ETAT_EXCEL_PARAM VALUES (null,null,%s,null,null,null)",[num_cet])
        #GET THE INTENATIONAL LIST
        if type_data == 'br' :
            view_int = 'Select * from  dmy.CNA_ALL_BR_INT ' 
            view_nat = "Select * from  dmy.CNA_ALL_BR_NAT "
        if type_data == 'se' :
            view_int = 'Select x.CNA_ORDER , x.NAME ,x.PRIME ,x.SINISTRE_REGLE ,x.SAP ,x.IS_TOTAL from  dmy.CNA_ALL_SEG_INT x ' 
            view_nat = "Select x.CNA_ORDER , x.NAME ,x.PRIME ,x.SINISTRE_REGLE ,x.SAP ,x.IS_TOTAL from  DMY.CNA_ALL_SEG_NAT x  "
        cursor.execute(view_int)
        page3= cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                    liste1.append(str(cell_data))
            liste_inter.append(liste1)
        #GET THE NATIONAL LIST
        cursor.execute(view_nat)
        page4= cursor.fetchall()
        for row_num, columns in enumerate(page4):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                    liste1.append(str(cell_data))
            liste_nat.append(liste1)
  
    #return render(request, 'main/templates/main.html')
    responseData = {
        'type_data' : type_data,
        'liste_inter' : liste_inter,
        'liste_nat' : liste_nat
    }
    return JsonResponse(responseData)

#RETURNS THE WHERE CLAUSE FOR THE IBNR MATRICE PAGE 
def where_clause(br , zone , port) :
    "RETURNS THE WHERE CLAUSE FOR THE IBNR MATRICE PAGE"
    where = 'WHERE '
    liste_where = []
    where_br = 'vide'
    where_zone = 'vide'
    where_port = 'vide'
    if (br is None and zone is None and port is None) or  (br == '?' and zone == '?' and port == '?') :
        return ' ' 
    else :
        if br != '?' : 
            where_br = "x.BRANCHE = '"+br+"' "
            liste_where.append(where_br)
        if zone != '?' :
            where_zone = "x.ZONE = '"+zone+"' "
            liste_where.append(where_zone)
        if port != '?' :
            where_port = "x.PORTFOLIO_TYPE = '"+port+"' "
            liste_where.append(where_port)
        i = 0 
        for x in liste_where : 
            if i == 0 :
                where = where + x
            else :
                where = where +" and " + x
            i = i+1 
        return  where 

def decoderCodeView(code , annee) :
    "RETURNS THE VIEW NAME"
    if code == '001A' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.CET_EXCEL_ACC_NEW_DESIGN cea"
        else :
            return "DMY.CET_EXCEL_ACC cea"
    if code == '001R' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.CET_EXCEL_RETRO_NEW_DESIGN cea"
        else :
            return "DMY.CET_EXCEL_RETRO cea"
    if code == '002A' :
        return "DMY.CET_EXCEL_PRIME cea"
    if code == '001S' :
        return "DMY.CET_EXCEL_SINISTRE cea"
    if code == '00RA' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.CET_EXEL_REC_ACC_NEW_DESIGN cea"
        else :
            return "DMY.CET_EXEL_REC_ACC cea"
    if code == '00RR' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.CET_EXEL_REC_RETRO_NEW_DESIGN cea"
        else : 
            return "DMY.CET_EXEL_REC_RETRO cea"
    if code == '00SA' :
        return "DMY.CET_EXCEL_SAP cea"
    if code == 'TR1A' :
        return "DMY.CET_EXCEL_ACC_TR cea"
    if code == 'TR1R' :
        return "DMY.CET_EXCEL_RETRO_TR cea"
    if code == 'DT2A' :
        return "DMY.CET_EXCEL_PRIME cea"
    if code == 'DT1S' :
        return "DMY.CET_EXCEL_SINISTRE cea"
    if code == 'TRRA' :
        return "DMY.CET_EXCEL_REC_ACC_TR cea"
    if code == 'TRRR' :
        return "DMY.CET_EXCEL_REC_RETRO_TR cea"
    if code == 'DTSA' :
        return "DMY.CET_EXCEL_SAP cea"
    if code == '003R' :
        return "DMY.CET_EXCEL_PRIME_RETRO cea"
    if code == 'DT3R' :
        return "DMY.CET_EXCEL_PRIME_RETRO cea"
    if code == '002R' :
        return "DMY.CET_EXCEL_SINISTRE_RETRO cea"
    if code == 'DT2R' :
        return "DMY.CET_EXCEL_SINISTRE_RETRO cea"
    if code == '00SR' :
        return "DMY.CET_EXCEL_SAP_RETRO cea"
    if code == 'DTSR' :
        return "DMY.CET_EXCEL_SAP_RETRO cea"
    if code == '00KPMG' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.ERM_EXCEL_KPMG_ACC_NEW_DESIGN cea"
        else :
            return "DMY.ERM_EXCEL_KPMG_ACC cea"
    if code == '00KPMGR' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.ERM_EXCEL_KPMG_R_NEW_D cea"
        else :
            return "DMY.ERM_EXCEL_KPMG_RETRO cea"
        
    if code == '00ERM_P' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.ERM_PRIME_RETRO_PART_N_D cea"
        else :
            return "DMY.ERM_PRIME_RETRO_PARTICIPANT cea "
    if code == '00ERM_SAP' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.ERM_SAP_RETRO_PART_N_D cea"
        else :
            return "DMY.ERM_SAP_RETRO_PARTICIPANT cea "
        
    if code == '00ERM_SIN' :
        if int(annee) > 2020 : #IN ORDER TO USE THE NEW TABLES IN DMY SCHEMA
            return "DMY.ERM_SIN_RETRO_PART_N_D cea"
        else :
            return "DMY.ERM_SIN_RETRO_PARTICIPANT cea "
    if code == '00GEN_DEPOT' :
        return "DMY.GENERAL_DEPOT_ACC cea "
    if code == '00GEN_DEPOT_RETRO' :
        return "DMY.GENERAL_DEPOT_RETRO cea "
    if code == '01GEN_LIABI' :
        return "DMY.GENERAL_LIABILITY_EPI_ACC cea "
    if code == '02OUT' :
        return "DMY.GENERAL_OUTSTANDING_ACC cea "
    if code == '03OUT_RETRO' :
        return "DMY.GENERAL_OUTSTANDING_RETRO cea "

def getNomFichier(code) :
    "RETURNS THE FILE NAME FOR A SPECIFIC EXCEL STATE"
    if code == '001A' :
        return "Etat CET Details Acceptation"
    if code == '001R' :
        return "Etat CET Details Retrocession"
    if code == '002A' :
        return "Etat CET Details Prime"
    if code == '001S' :
        return "Etat CET Details Sinistre"
    if code == '00RA' :
        return "Etat CET Details REC Acceptation"
    if code == '00RR' :
        return "Etat CET Details REC Retrocession"
    if code == '00SA' :
        return "Etat CET Details SAP"
    if code == 'TR1A' :
        return "Etat CET Details Acceptation"
    if code == 'TR1R' :
        return "Etat CET Details Retrocession"
    if code == 'DT2A' :
        return "Etat CET Details Prime"
    if code == 'DT1S' :
        return "Etat CET Details Sinistre"
    if code == 'TRRA' :
        return "Etat CET Details REC Acceptation"
    if code == 'TRRR' :
        return "Etat CET Details REC Retrocession"
    if code == 'DTSA' :
        return "Etat CET Details SAP"
    if code == '003R' :
        return "Etat CET Details Prime Retro"
    if code == 'DT3R' :
        return "Etat CET Details Prime Retro"
    if code == '002R' :
        return "Etat CET Details Sinistre"
    if code == 'DT2R' :
        return "Etat CET Details Sinistre"
    if code == '00SR' :
        return "Etat CET Details Sap Retro"
    if code == 'DTSR' :
        return "Etat CET Details Sap Retro"
    if code == '00KPMG' :
        return "ETAT KPMG ACCPETATION"
    if code == '00KPMGR' :
        return "ETAT KPMG RETROCESSION"
    if code == '00ERM_P' :
        return "ETAT PRIME RETRO PAR PARTICIPANT"
    if code == '00ERM_SAP' :
        return "ETAT SAP RETRO PAR PARTICIPANT"
    if code == '00ERM_SIN' :
        return "ETAT SINISTRE RETRO PAR PARTICIPANT"
    if code == '00GEN_DEPOT' :
        return "ETAT DEPOT ACCEPTATION"
    if code == '00GEN_DEPOT_RETRO' :
        return "ETAT DEPOT RETROCESSION"
    if code == '01GEN_LIABI' :
        return "ETAT LIABILITY EPI ACCEPTATION"
    if code == '02OUT' :
        return "ETAT OUTSTANDING ACCEPTATION"
    if code == '03OUT_RETRO' :
        return "ETAT OUTSTANDING RETROCESSION"

def decoderSouscriton(type):
    "RETURNS THE SOUSCRIPTION NAME"
    if type =='A':
        return 'ACCEPTATION'
    elif type == 'R' :
        return 'RETROCESSION'
    elif type == 'N':
        return 'NET'

def decoderZone(type):
    "RETURNS THE ZONE NAME"
    if type =='1':
        return 'ALGERIE'
    elif type == '2' :
        return 'AFRIQUE ET MONDE ARABE'
    elif type == '3':
        return 'AMERIQUE ET ASIE'
    elif type =='4':
        return 'EUROPE'
    elif type == '*' :
        return 'AFFAIRES INTERNATIONALES'
    elif type == '?':
        return 'TOUTES ZONES'

def decoderBranche(type):
    with connection.cursor() as cursor:
        cursor.execute ("SELECT bc.BRANCH_NAME FROM DOP.BRANCHES_CET bc WHERE bc.BRANCH_GROUP_CODE =  %s ",[type])
        row = cursor.fetchone()
        data = row[0]
    return(data) 

def decoderBrancheTakaful(type):
    "RETURNS THE BRANCH NAME OF TAKAFUL BRANCHES"
    with connection.cursor() as cursor:
        cursor.execute ("SELECT bc.BRANCH_NAME FROM DOP.BRANCHES_CET bc WHERE bc.BRANCH_GROUP_CODE =  %s ",[type])
        row = cursor.fetchone()
        data = row[0]
        if type != '?' :
            data = data+" RETAKAFUL"
    return(data)
    
#Return all fields names from a cursor as a list
def dictfetchall(cursor):
    "Return all fields names from a cursor as a list"
    columns = [col[0] for col in cursor.description]
    """return [
        dict(zip(columns, row))
        for row in cursor.fetchall()
    ]
    """
    return columns

#RETURNS THE DATA OF IBNR FOR ALL THE PORTFOLIO TYPES
def ibnr_display (request ,branche):
    "RETURNS THE TABLE OF IBNR FOR ALL THE PORTFOLIO TYPES"
    where_clause=''
    liste_branches =[]
    totale_avant_ibnr = 0
    totale_ibnr = 0
    totale_apres_ibnr = 0

    totale_avant_ibnr_traite = 0
    totale_ibnr_traite = 0
    totale_apres_ibnr_traite = 0

    totale_avant_ibnr_fac = 0
    totale_ibnr_fac = 0
    totale_apres_ibnr_fac = 0

    totale_avant_ibnr_display = 0
    totale_ibnr_display = 0
    totale_apres_ibnr_display = 0
    """if request.method == 'GET':
        branche = request.GET.get('branche')"""
    
    if branche is None :
        branche ="FIRE"
    liste_sap = []
    liste_sap_traite =[]
    liste_sap_fac = []
    test =''
    condition = False
    message = ''
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM DMY.IBNR_PARAMETRE ip WHERE ip.BRANCHE =%s",[branche])
        row_of_param = cursor.fetchone()
        param_traite = row_of_param[2]
        param_fac = row_of_param[3]
        
        cursor.execute("SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp ")
        row =cursor.fetchone()
        CET_EN_COURS = row[0]
        cursor.execute("SELECT * FROM dmy.CET_PERIODE cp WHERE cp.NUM_CET = %s ",[CET_EN_COURS])
        row2 = cursor.fetchone()
        if row2 is  not None : 
            test = row2[0]
            if  test : 
                message = 'Le cet est insérer !!'
                condition = True
            else :
                message = 'Veuillez insrer le cet 1 !!' #USELESS DELETE IT 
        else :
            message = 'Veuillez insrer le cet 2 !!'
            condition = False
            # INITIALIZE THE CONTEXT PARAMETERS (WICH WILL NOT BE USER BECAUSE IN THIS CASE THE CET IS ALREADY INSERTED)
            traite = 1 
            fac = 1
            zone_algerie = 1
            zone_europe = 1
            zone_amerique_asie = 1
            zone_afrique = 1
    if param_traite == '1' and param_fac =='0' :
        where_clause =" AND id.PORTFOLIO_TYPE =1"
    if param_traite == '0' and param_fac =='1' :
        where_clause =" AND id.PORTFOLIO_TYPE =2"

    if condition :
        
        # get data with the two PORTFOLIO_TYPE
        with connection.cursor() as cursor:
            cursor.execute("""  
            SELECT 	
                    aa.BRANCHE ,
                    aa.UNDERWRITING_YEAR ,
                    sum(aa.SAP) ,
                    sum(aa.ibnr),
                    sum(aa.sap_ibnr) , 
                    max(aa.taux)

            FROM (

            SELECT 	--id.ID ,
                                                    id.BRANCHE ,
                                                    id.UNDERWRITING_YEAR ,
                                                    sum(id.SAP)  AS sap ,
                                                    sum(id.ibnr) AS ibnr,
                                                    sum(id.sap_ibnr) AS sap_ibnr , 
                                                    id.taux

                                            FROM DMY.IBNR_DETAIL id
                                            LEFT JOIN dop.BRANCHES_CET bc ON
                                            bc.BRANCH_NAME = id.BRANCHE
                                            WHERE id.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)
                                            and id.PORTFOLIO_TYPE = 1 
                                            AND id.BRANCHE =%s
                                            GROUP BY 
                                                    id.BRANCHE ,
                                                    id.UNDERWRITING_YEAR  , 
                                                    id.taux
                                        UNION 

                                        SELECT 	--id.ID ,
                                                    id.BRANCHE ,
                                                    id.UNDERWRITING_YEAR ,
                                                    sum(id.SAP) AS sap ,
                                                    sum(id.ibnr) AS ibnr ,
                                                    sum(id.sap_ibnr)  AS sap_ibnr, 
                                                    id.taux

                                            FROM DMY.IBNR_DETAIL id
                                            LEFT JOIN dop.BRANCHES_CET bc ON
                                            bc.BRANCH_NAME = id.BRANCHE
                                            WHERE id.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)
                                            and id.PORTFOLIO_TYPE = 2
                                            AND id.BRANCHE =%s
                                            GROUP BY 
                                                    --id.ID , 
                                                    id.BRANCHE ,
                                                    id.UNDERWRITING_YEAR  , 
                                                    id.taux		                                
                                                    ) aa
                                                    
                                    GROUP BY aa.BRANCHE ,
                                                    aa.UNDERWRITING_YEAR 
                                    ORDER BY     aa.BRANCHE ,
                                                    aa.UNDERWRITING_YEAR
                                 """  ,[branche,branche])
            page = cursor.fetchall()
            for row_num, columns in enumerate(page):
                liste =[]
                for col_num, cell_data in enumerate(columns):
                    if not isinstance(cell_data,str) and (col_num ==2 or col_num ==3 or col_num ==4 ):
                        if col_num ==2 :
                            totale_avant_ibnr = totale_avant_ibnr +cell_data
                        if col_num ==3 :
                            totale_ibnr = totale_ibnr +cell_data
                        if col_num ==4 :
                            totale_apres_ibnr = totale_apres_ibnr +cell_data

                    if (col_num ==5) :
                        cell_data = '{:,.10f}'.format(cell_data).replace(',', ' ')
                    liste.append(str(cell_data))
                liste_sap.append(liste)
        # get data with the  PORTFOLIO_TYPE = 1 
            cursor.execute("""  SELECT 	--id.ID ,
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR ,
                                        sum(id.SAP) ,
                                        sum(id.ibnr),
                                        sum(id.sap_ibnr) , 
		                                id.taux

                                FROM DMY.IBNR_DETAIL id
                                LEFT JOIN dop.BRANCHES_CET bc ON
                                bc.BRANCH_NAME = id.BRANCHE
                                WHERE id.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)
                                and id.PORTFOLIO_TYPE = 1 
                                AND id.BRANCHE =%s
                                GROUP BY 
                                        --id.ID , 
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR  , 
		                                id.taux

                                ORDER BY--id.ID ,
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR , 
		                                id.taux
                                 """  ,[branche])
            page_traite = cursor.fetchall()
            for row_num, columns in enumerate(page_traite):
                liste_traite =[]
                for col_num, cell_data in enumerate(columns):
                    if not isinstance(cell_data,str) and (col_num ==2 or col_num ==3 or col_num ==4 ):
                        if col_num ==2 :
                            totale_avant_ibnr_traite = totale_avant_ibnr_traite +cell_data
                        if col_num ==3 :
                            totale_ibnr_traite = totale_ibnr_traite +cell_data
                        if col_num ==4 :
                            totale_apres_ibnr_traite = totale_apres_ibnr_traite +cell_data

                    if (col_num ==5) :
                        cell_data = '{:,.10f}'.format(cell_data).replace(',', ' ')
                    liste_traite.append(str(cell_data))
                liste_sap_traite.append(liste_traite)

            
            # get data with the  PORTFOLIO_TYPE = 2 
            cursor.execute("""  SELECT 	--id.ID ,
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR ,
                                        sum(id.SAP) ,
                                        sum(id.ibnr),
                                        sum(id.sap_ibnr) , 
		                                id.taux

                                FROM DMY.IBNR_DETAIL id
                                LEFT JOIN dop.BRANCHES_CET bc ON
                                bc.BRANCH_NAME = id.BRANCHE
                                WHERE id.NUM_CET = (SELECT scp.CET_EN_COURS FROM DMY.CET_PARAMETRES scp)
                                and id.PORTFOLIO_TYPE = 2
                                AND id.BRANCHE =%s
                                GROUP BY 
                                        --id.ID , 
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR  , 
		                                id.taux

                                ORDER BY--id.ID ,
                                        id.BRANCHE ,
                                        id.UNDERWRITING_YEAR , 
		                                id.taux
                                 """  ,[branche])
            page_fac = cursor.fetchall()
            for row_num, columns in enumerate(page_fac):
                liste_fac =[]
                for col_num, cell_data in enumerate(columns):
                    if not isinstance(cell_data,str) and (col_num ==2 or col_num ==3 or col_num ==4 ):
                        if col_num ==2 :
                            totale_avant_ibnr_fac = totale_avant_ibnr_fac +cell_data
                        if col_num ==3 :
                            totale_ibnr_fac = totale_ibnr_fac +cell_data
                        if col_num ==4 :
                            totale_apres_ibnr_fac = totale_apres_ibnr_fac +cell_data

                    if (col_num ==5) :
                        cell_data = '{:,.10f}'.format(cell_data).replace(',', ' ')
                    liste_fac.append(str(cell_data))
                liste_sap_fac.append(liste_fac)


           
            cursor.execute("SELECT DISTINCT id.BRANCHE FROM dmy.IBNR_DETAIL id ORDER BY id.BRANCHE ")   
            rows_branche = cursor.fetchall()
            for row_num, columns in enumerate(rows_branche):
                for col_num, cell_data in enumerate(columns):
                    liste_branches.append(cell_data)
            cursor.execute("SELECT * FROM DMY.IBNR_PARAMETRE ip WHERE ip.BRANCHE =%s ",[branche])
            param_row = cursor.fetchone()
            traite = param_row[2]
            fac = param_row[3]
            zone_algerie = param_row[4]
            zone_europe = param_row[5]
            zone_amerique_asie = param_row[6]
            zone_afrique = param_row[7]

    #SETUP WICH LIST IS GOING TO BE DISPLAYED 
    liste_sap_display =[]
    if param_traite == '1' and param_fac =='0' :
        liste_sap_display = liste_sap_traite
        totale_avant_ibnr_display = totale_avant_ibnr_traite
        totale_ibnr_display = totale_ibnr_traite
        totale_apres_ibnr_display = totale_apres_ibnr_traite
    if param_traite == '0' and param_fac =='1' :
        liste_sap_display = liste_sap_fac
        totale_avant_ibnr_display = totale_avant_ibnr_fac
        totale_ibnr_display = totale_ibnr_fac
        totale_apres_ibnr_display = totale_apres_ibnr_fac
    if param_traite == '1' and param_fac =='1' :
        liste_sap_display = liste_sap
        totale_avant_ibnr_display = totale_avant_ibnr
        totale_ibnr_display = totale_ibnr
        totale_apres_ibnr_display = totale_apres_ibnr

    # create data dictionary
    dataDictionary = {
        'liste_sap' : liste_sap,
        'liste_sap_traite' : liste_sap_traite ,
        'liste_sap_fac' : liste_sap_fac ,
    }
    # dump data
    dataJSON = json.dumps(dataDictionary)

    context = {
        'liste_branches' : liste_branches,
        'liste_sap' : liste_sap,
        'liste_sap_display' : liste_sap_display ,
        'message'  : message ,
        'condition' : condition,
        'data': dataJSON,
        'branche' : branche,

        'totale_avant_ibnr' : totale_avant_ibnr ,
        'totale_ibnr' : totale_ibnr ,
        'totale_apres_ibnr' : totale_apres_ibnr ,
        
        'totale_avant_ibnr_traite' : totale_avant_ibnr_traite ,
        'totale_ibnr_traite' : totale_ibnr_traite ,
        'totale_apres_ibnr_traite' : totale_apres_ibnr_traite ,
        
        'totale_avant_ibnr_fac' : totale_avant_ibnr_fac ,
        'totale_ibnr_fac' : totale_ibnr_fac ,
        'totale_apres_ibnr_fac' : totale_apres_ibnr_fac ,

        'totale_avant_ibnr_display' : totale_avant_ibnr_display ,
        'totale_ibnr_display' : totale_ibnr_display,
        'totale_apres_ibnr_display' : totale_apres_ibnr_display ,

        'traite' : traite ,
        'fac' : fac ,
        'zone_algerie' : zone_algerie ,
        'zone_europe' : zone_europe ,
        'zone_amerique_asie' : zone_amerique_asie ,
        'zone_afrique'  : zone_afrique
    }
    return(context )

#RETURN THE SUB QUERY ON THE PORTFOLIO TYPE FOR THE  UPDATE
def where_clause_portfolio (traite , fac ) :
    "RETURN THE SUB QUERY ON THE PORTFOLIO TYPE FOR THE  UPDATE"
    if ( ( traite == '1') and ( fac == '1')  ):
        return ( " and PORTFOLIO_TYPE IN (1,2) ")
    if ( ( traite == '1') and ( fac == '0')  ):
        return ( " and PORTFOLIO_TYPE = 1 ")
    if ( ( traite == '0') and ( fac == '1')  ):
        return ( " and PORTFOLIO_TYPE = 2 ")
    if ( ( traite == '0') and ( fac == '0')  ):
        return ( "  ")

#RETURN THE SUB QUERY ON THE ZONE FOR THE  UPDATE
def where_clause_zone (afrique ,amerique_asie , europe ) :
    "RETURN THE SUB QUERY ON THE ZONE FOR THE  UPDATE"
    if ( ( afrique == '1')  and ( amerique_asie == '1') and ( europe == '1') ):
        return ( " and ZONE_CODE IN (2,3,4) ")
    
    if ( ( afrique == '1')  and ( amerique_asie == '1') and ( europe == '0') ):
        return ( " and ZONE_CODE IN (2,3) ")

    if ( ( afrique == '1')  and ( amerique_asie == '0') and ( europe == '1') ):
        return ( " and ZONE_CODE IN (2,4) ")

    if ( ( afrique == '1')  and ( amerique_asie == '0') and ( europe == '0') ):
        return ( " and ZONE_CODE = 2  ")

    if ( ( afrique == '0')  and ( amerique_asie == '1') and ( europe == '1') ):
        return ( " and ZONE_CODE IN (3,4)  ")
    
    if ( ( afrique == '0')  and ( amerique_asie == '1') and ( europe == '0') ):
        return ( " and ZONE_CODE= 3   ")
    
    if ( ( afrique == '0')  and ( amerique_asie == '0') and ( europe == '1') ):
        return ( " and ZONE_CODE= 4   ")

    if ( ( afrique == '0')  and ( amerique_asie == '0') and ( europe == '0') ):
        return ( "  ")

#RETURNS A LIST CONTAINING THE DATE_DEBUT AND DATE_FIN ON THE CORRESPONDING CET 
def get_dates_cet (num_cet) :
    "RETURNS A LIST CONTAINING THE DATE_DEBUT AND DATE_FIN ON THE CORRESPONDING CET" 
    dates = []
    if num_cet >= 694 : #POUR LES CET DE 2021 ET PLUS
        with connection.cursor() as cursor:
            cursor.execute ("SELECT cp.DATE_DEBUT , cp.DATE_FIN FROM DMY.CET_PERIODE cp WHERE cp.NUM_CET = %s",[num_cet])
            page = cursor.fetchall()
            for row_num, columns in enumerate(page):
                for col_num, cell_data in enumerate(columns):
                    dates.append(cell_data)       
    else : #POUR LES CET d'avant 2021
        with connection.cursor() as cursor:
            cursor.execute ("SELECT ce.DATE_DEBUT , ce.DATE_FIN FROM dop.CET_ENTETE ce WHERE ce.ID_CET = %s",[num_cet])
            page = cursor.fetchall()
            for row_num, columns in enumerate(page):
                for col_num, cell_data in enumerate(columns):
                    dates.append(cell_data)
    return (dates)

#RETURNS THE LIST OF BRANCHES 
def get_branches_cet(format) : 
    "RETURNS THE LIST OF BRANCHES" 
    liste_branches = []
    if format == 'code' :
        with connection.cursor() as cursor:
                cursor.execute ("SELECT bc.BRANCH_GROUP_CODE FROM DOP.BRANCHES_CET bc WHERE bc.BRANCH_GROUP_CODE <> '?' ORDER BY bc.BRANCH_GROUP_CODE  ")
                page= cursor.fetchall()
                for row_num, columns in enumerate(page):
                    for col_num, cell_data in enumerate(columns):
                            liste_branches.append(str(cell_data))
        liste_branches.append('?')            
    if format == 'classique' :
        with connection.cursor() as cursor:
                cursor.execute ("SELECT * FROM DOP.BRANCHES_CET bc ORDER BY bc.BRANCH_GROUP_CODE ")
                page= cursor.fetchall()
                for row_num, columns in enumerate(page):
                    liste1 =[]
                    for col_num, cell_data in enumerate(columns):
                            liste1.append(str(cell_data))
                    liste_branches.append(liste1)
    if format == 'dashbord' :
        with connection.cursor() as cursor:
                cursor.execute ("""SELECT rownum-1,tt.* FROM 
                                (SELECT  bc.BRANCH_NAME FROM DOP.BRANCHES_CET bc WHERE bc.BRANCH_GROUP_CODE <> '?' ORDER BY bc.BRANCH_GROUP_CODE)tt
                                UNION 
                                SELECT 24 , 'TOUTES BRANCHES' FROM dual """)
                page= cursor.fetchall()
                for row_num, columns in enumerate(page):
                    liste1 =[]
                    for col_num, cell_data in enumerate(columns):
                            liste1.append(str(cell_data))
                    liste_branches.append(liste1)
    if format == 'excel' :
        with connection.cursor() as cursor:
                cursor.execute ("SELECT bc.BRANCH_NAME , bc.BRANCH_NAME   FROM DOP.BRANCHES_CET bc WHERE bc.BRANCH_GROUP_CODE <> '?'  ORDER BY bc.BRANCH_GROUP_CODE")
                page= cursor.fetchall()
                for row_num, columns in enumerate(page):
                    liste1 =[]
                    for col_num, cell_data in enumerate(columns):
                            liste1.append(str(cell_data))
                    liste_branches.append(liste1)
                liste_branches.append(['?','TOUTES BRANCHES'])
    return liste_branches

#RETURNS THE LIST OF DIRECTIONS 
def get_directions() : 
    "RETURNS THE LIST OF DIRECTIONS"
    liste_directions = []
    with connection.cursor() as cursor:
        cursor.execute("SELECT * FROM DMY.CET_DIRECTIONS cd ")
        page3= cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                    liste1.append(str(cell_data))
            liste_directions.append(liste1)
    liste_directions.append(['?','Toutes Directions'])
    return(liste_directions)

#RETURNS THE WHERE CLAUSE OF THE EXCEL QUERY
def get_sub_profit_center_code(direction):
    "RETURNS THE WHERE CLAUSE OF THE EXCEL QUERY"
    liste_code_sub = []
    with connection.cursor() as cursor:
        cursor.execute("""SELECT cspcc.SUB_PROFIT_CENTRE_CODE FROM dmy.CET_DIRECTION_SUB_PROFIT cdsp 
                            JOIN DMY.CET_DIRECTIONS cd ON CDSP.ID_DIRECTION = cd.id
                            JOIN DMY.CET_SUB_PROFIT_CENTRE_CODE cspcc ON cspcc.ID = CDSP .ID_SUB_PROFIT 
                            WHERE cd.ID = %s """,[direction])
        page3= cursor.fetchall()
        for row_num, columns in enumerate(page3):
            liste1 =[]
            for col_num, cell_data in enumerate(columns):
                    liste_code_sub.append(str(cell_data))
            #liste_code_sub.append(liste1)
           # cea.SUB_PROFIT_CENTRE_CODE IN ('I1','I2','I3','R1','R2') "
    where = "cea.SUB_PROFIT_CENTRE_CODE IN ("
    for x in liste_code_sub : 
        where = where +"'"+ x +"',"
    where = where[:-1]
    where = where+")"
    return(where)

"""
FRONT + BACK END : DJEMA MOHAMED YACINE
DATA BASE : TOUBALINE MOHAMED , DJEMA MOHAMED YACINE
"""
