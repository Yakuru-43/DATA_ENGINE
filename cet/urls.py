from . import views
from django.conf.urls import include, url
from django.views.static import serve 
from django.conf import settings
from django.contrib.auth import views as auth_views
from .views import PasswordsChangeView
from django.urls import include, path
app_name = 'cet'

urlpatterns = [
    url(r'^$', views.index),

    url(r'^test/$', views.Reviewview.as_view() , name='test'),

    path('get_segments_branches/', views.get_segments_branches, name='get_segments_branches'),
    path('segments_update/', views.segments_update, name='segments_update'),
    path('segments_delete/', views.segments_delete, name='segments_delete'),
    path('segments_br_add/', views.segments_br_add, name='segments_br_add'),
    
    url(r'^redirectDev/$', views.redirectDev, name='redirectDev'),
    url(r'^pdf/$', views.pdf, name='pdf'), 
    url(r'^ibnr/$', views.view_ibnr, name='view_ibnr'),
    url(r'^ibnr_save/$', views.ibnr_save, name='ibnr_save'),
    url(r'^ibnr_reinitialiser/$', views.ibnr_reinitialiser, name='ibnr_reinitialiser'),
    url(r'^apercu_ibnr/$', views.apercu_ibnr, name='apercu_ibnr'),
    url(r'^resume_ibnr/$', views.resume_ibnr, name='resume_ibnr'),
    url(r'^valider_ibnr/$', views.valider_ibnr, name='valider_ibnr'),
    url(r'^view_matrice_dev/$', views.view_matrice_dev, name='view_matrice_dev'),
    url(r'^excel_matrice_ibnr/$', views.excel_matrice_ibnr, name='excel_matrice_ibnr'),
    url(r'^excel_bloc_matrice_ibnr/$', views.excel_bloc_matrice_ibnr, name='excel_bloc_matrice_ibnr'),
    url(r'^excel/$', views.excelview2, name='excel'),
    url(r'^excel_test/$', views.excelview, name='excel_test'),
    url(r'^dashboard/$', views.dashboard, name='dashboard'),
    url(r'^pdftakaful/$', views.pdftakaful, name='pdftakaful'),
    url(r'^authentification/$', views.authentification, name='authentification'),
    url(r'^login/$', views.login_redirect, name='redirect'),
    url(r'^logout_view/$', views.logout_view, name='logout_view'),
    url(r'^genererpdf/$', views.genererpdf, name='genererpdf'),
    url(r'^genererpdftakaful/$', views.genererpdftakaful, name='genererpdftakaful'),
    url(r'^sauvegarderpdf/$', views.sauvegarderpdf, name='sauvegarderpdf'),
    url(r'^etatsexcel/$', views.etatsexcel, name='etatsexcel'),
    url(r'^kpi/$', views.kpi_view, name='kpi'),
    url(r'^kri/$', views.kri_view, name='kri'),
    url(r'^etatsexcelerm/$', views.etatsexcelerm, name='etatsexcelerm'),

    url(r'^etatsexcelgen/$', views.etatsexcelgen, name='etatsexcelgen'),

    url(r'^etatsexcelcna/$', views.etatsexcelcna, name='etatsexcelcna'),
    url(r'^tableaux_cna/$', views.tableaux_cna, name='tableaux_cna'),

    url(r'^top_list/$', views.top_list, name='top_list'),
    url(r'^management/$', views.management, name='management'),
    url(r'^super_management/$', views.super_management, name='super_management'),
    url(r'^cet_suivant/$', views.cet_suivant, name='cet_suivant'),
    url(r'^bloquer_rms/$', views.bloquer_rms, name='bloquer_rms'),
    url(r'^debloquer_rms/$', views.debloquer_rms, name='debloquer_rms'),
    url(r'^bloquer_user/$', views.bloquer_user, name='bloquer_user'),
    url(r'^debloquer_user/$', views.debloquer_user, name='debloquer_user'),
    url(r'^egal_equi/$', views.view_egal_equi, name='view_egal_equi'),
    url(r'^save_taux_egal_equi/$', views.save_taux_egal_equi, name='save_taux_egal_equi'),
    url(r'^apercu_prov_egal_equi/$', views.apercu_prov_egal_equi, name='apercu_prov_egal_equi'),
    url(r'^valider_prov_egal_equi/$', views.valider_prov_egal_equi, name='valider_prov_egal_equi'),

    
    url(r'^view_changement_mdp/$', PasswordsChangeView.as_view(template_name='main/templates/securite.html') , name='view_changement_mdp'),
    url(r'^password_change_done/$', views.success_change_password , name='success_change_password'),
]

"""views.test"""