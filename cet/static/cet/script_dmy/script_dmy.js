/*$("#boxTraite").change(function(){
        var value_traite = $('#boxTraite').is(':checked'); 
        if ( value_traite == true ) message = 'Vous avez sélectionner le type de souscription traité, cliquer sur CONFIRMER, pour prendre en compte ce type de souscription dans les SAP affichée.IMPORTANT : les taux IBNR seront réinitialisé '
        else message = 'Vous avez désélectionner le type de souscription traité, cliquer sur CONFIRMER, pour ne plus prendre en compte ce type de souscription dans les SAP affichée. IMPORTANT : les taux IBNR seront réinitialisé. '
        $.confirm({
                    title: 'Attention !',
                    content: message ,
                    buttons: {
                      Confirmer: {
                            text: 'Confirmer',
                            btnClass: 'btn-blue',
                            action: function(){
                              var branche = $('#branche_hidden').val();
                              if (value_traite){
                                var traite = 1
                              }
                              else {
                                var traite = 0
                              }
                              if ($('#boxFac').is(':checked')){
                                var fac = 1
                              }
                              else {
                                var fac = 0
                              }
                              window.location.href = "{% url 'cet:test' %}?branche="+branche+"&traite="+traite+"&fac="+fac;
                            }
                        },
                        Annuler:{ 
                        btnClass: 'btn-red',
                        action: function(){
                              if (value_traite ){
                                $('#boxTraite').prop('checked', false);
                              } 
                              else{
                                $('#boxTraite').prop('checked', true);
                              }
                            }
                        }    
                    }
                    });
        })*/


        $('input:checkbox').change(function(){
          var data = JSON.parse("{{data|escapejs}}");
          var value_traite = $('#boxTraite').is(':checked'); 
          var value_fac = $('#boxFac').is(':checked'); 
          // ONLY TRAITE
          if ( ( value_traite == true ) && ( value_fac == false ) ){
              for (var i =1; i<17 ; i++ ){
              $("#col1_ligne"+i).html(formatNumber( data["liste_sap_traite"][(i-1)][2] ));  
              $("#col2_ligne"+i).html(0) ;
              $("#col3_ligne"+i).html(data["liste_sap_traite"][(i-1)][4]) ;
              $("#col4_ligne"+i).val("1.0000000000") ;
            }
              
          }
          // ONLY FAC 
          if ( ( value_traite == false ) && ( value_fac == true ) ){
              for (var i =1; i<17 ; i++ ){
              $("#col1_ligne"+i).html(formatNumber( data["liste_sap_fac"][(i-1)][2] ));  
              $("#col2_ligne"+i).html(0) ;
              $("#col3_ligne"+i).html(data["liste_sap_fac"][(i-1)][4]) ;
              $("#col4_ligne"+i).val("1.0000000000") ;
            }
           
          }
          //BOTH TRAITE AND FAC 
          if ( ( value_traite == true ) && ( value_fac == true ) ){
              for (var i =1; i<17 ; i++ ){
              $("#col1_ligne"+i).html(formatNumber( data["liste_sap"][(i-1)][2] ));  
              $("#col2_ligne"+i).html(0) ;
              $("#col3_ligne"+i).html(data["liste_sap"][(i-1)][4]) ;
              $("#col4_ligne"+i).val("1.0000000000") ;
            }            
          }
          //NONE OF THEM
          if ( ( value_traite == false ) && ( value_fac == false ) ){
            $('#boxFac').prop('checked', true);
            $('#boxTraite').prop('checked', true);
            for (var i =1; i<17 ; i++ ){
              $("#col1_ligne"+i).html(formatNumber( data["liste_sap"][(i-1)][2] ));  
              $("#col2_ligne"+i).html(0) ;
              $("#col3_ligne"+i).html(data["liste_sap"][(i-1)][4]) ;
              $("#col4_ligne"+i).val("1.0000000000") ;
            }  
            $.alert({
                      title: 'ATTENTION!',
                      content: 'Vous avez déséléctionné les deux types de souscritions. Vous devez toujours garder au moin un type de souscription selectionné!',
                      animation: 'top',
                      closeAnimation: 'bottom'
                    });
          }
         
          function formatNumber(num) {
            return num.toString().replace(/(\d)(?=(\d{3})+(?!\d))/g, '$1 ')
        }
          
        })
      

        /*$("#boxFac").change(function(){
        var value_fac = $('#boxFac').is(':checked'); 
        if ( value_fac == true ) message = 'Vous avez sélectionner le type de souscription facultative, cliquer sur CONFIRMER, pour prendre en compte ce type de souscription dans les SAP affichée pour cette branche.IMPORTANT : les taux IBNR seront réinitialisé '
        else message = 'Vous avez désélectionner le type de souscription facultative, cliquer sur CONFIRMER, pour ne plus prendre en compte ce type de souscription dans les SAP affichée pour cette branche. IMPORTANT : les taux IBNR seront réinitialisé. '
        $.confirm({
                    title: 'Attention !',
                    content: message ,
                    buttons: {
                      Confirmer: {
                            text: 'Confirmer',
                            btnClass: 'btn-blue',
                            action: function(){
                              var branche = $('#branche_hidden').val();
                              if (value_fac){
                                var fac = 1
                              }
                              else {
                                var fac = 0
                              }
                              if ($('#boxTraite').is(':checked')){
                                var traite = 1
                              }
                              else {
                                var traite = 0
                              }
                              window.location.href = "{% url 'cet:test' %}?branche="+branche+"&traite="+traite+"&fac="+fac;
                            }
                        },
                        Annuler:{ 
                        btnClass: 'btn-red',
                        action: function(){
                              if (value_fac ){
                                $('#boxFac').prop('checked', false);
                              } 
                              else{
                                $('#boxFac').prop('checked', true);
                              }
                            }
                        }    
                    }
                    });
        })
*/

     $('#btnDeco').confirm({
          title: 'Attention',
          content: 'Voulez vous vraiment vous déconnectez ?',
          animation: 'top',
          closeAnimation: 'bottom',
          buttons: {
              Confimer: {
              btnClass: 'btn-blue',
              action : function () {
                location.href = this.$target.attr('att');
              },
            },
              Annuler:{ 
              btnClass: 'btn-red',
            }   
          }
      });
      $('button[type=submit5]').confirm({
          title: 'Attention !',
          content: 'Tout travail non sauvegarder sera perdu, voulez vous continuer ?',
          animation: 'top',
          closeAnimation: 'bottom',
          buttons: {
              Confimer: {
              btnClass: 'btn-blue',
              action : function () {
                $('.myform').submit();
              },
            },
              Annuler:{ 
              btnClass: 'btn-red',
            }   
          }
      });
      $('button[type=submit_reset]').confirm({
          title: 'Attention !',
          content: 'Voulez vous vraiment réinitialiser les IBNR pour cette branche ?',
          animation: 'top',
          closeAnimation: 'bottom',
          buttons: {
              Confimer: {
              btnClass: 'btn-blue',
              action : function () {
                $('.reset_form').submit();
              },
            },
              Annuler:{ 
              btnClass: 'btn-red',
            }   
          }
      });



      $('button[type=submit1]').confirm({
          title: 'Attention !',
          content: 'Voulez vous vraiment sauvegarder les IBNR pour cette branche ?',
          animation: 'top',
          closeAnimation: 'bottom',
          buttons: {
              Confimer: {
              btnClass: 'btn-blue',
              action : function () {
                var previous_traite = JSON.parse("{{traite|escapejs}}");
                var previous_fac = JSON.parse("{{fac|escapejs}}");
                var condition = $('#conditionFil').val(); 
                var vrai_condition = false ;
                var condition_traite = false ;
                var condition_fac = false ;
                var CheckedFac = $('#boxFac').is(':checked'); 
                var CheckedTraite = $('#boxTraite').is(':checked'); 
                var CheckedEurope = $('#zone_europe').is(':checked'); 
                var CheckedAfrique = $('#zone_afrique').is(':checked'); 
                var CheckedAmerique = $('#zone_amerique_asie').is(':checked'); 
                if (previous_traite == "1") {condition_traite = true ;} 
                if (previous_fac == "1") {condition_fac = true ;} 
                if (condition == "2"){
                  vrai_condition = ( (CheckedFac == true) || (CheckedTraite == true ) );
                }
                else {
                  vrai_condition = ( ( (CheckedFac == true) || (CheckedTraite == true ) ) && ( (CheckedEurope == true) || (CheckedAfrique == true ) || (CheckedAmerique == true ) )  );
                }
                if  (vrai_condition)
                {
            
                  if ( (condition_fac != CheckedFac) || ( (condition_traite != CheckedTraite)) ){ 

                   
                    $.confirm({
                    title: 'Attention !',
                    animation: 'top',
                    closeAnimation: 'bottom',
                    content: 'Attention, Vous avez changé le type de souscription, les IBNR seront uniquement apppliqué au(x) type(s) de souscription(s) choisie pour cette branche.' ,
                    buttons: {
                      Confirmer: {
                            text: 'Confirmer',
                            btnClass: 'btn-blue',
  
                            action: function(){
                              $('.save_form').submit();
                            }
                        },
                        Annuler:{ 
                        btnClass: 'btn-red',
                      } 
                        
                    }
                    });
   
                  }
                  else{
                    $('.save_form').submit();
                  }
                }
                else {
                  if (condition == "2"){
                    this.setContent('Vous devez cocher au moin un type de souscription.');
                  }
                  if (condition == "1"){
                    this.setContent('Vous devez cocher au moin une zone et un type de souscription.');
                  }
                  this.buttons.Confimer.hide();
                  return(false);
                } 
              },
            },
              Annuler:{ 
              btnClass: 'btn-red',
            }   
          }
      });



      $('button[type=submit3]').confirm({
          title: 'Attention !',
          content: 'Voulez vous vraiment insérer le CET dans la base de donnée ?',
          animation: 'top',
          closeAnimation: 'bottom',
          buttons: {
              Confimer: {
              btnClass: 'btn-blue',
              action : function () {
                $('.save_pdf').submit();
              },
            },
              Annuler:{ 
              btnClass: 'btn-red',
            }   
          }
      });
      /*
      $(document).ready(function () {

          $('#myform').validate({
            submitHandler : function(form) {
              if (confirm("Voulez vous vraiment sauvegarder les IBNR pour cette branche ?")) {
                form.submit();
               }
          },
          rules: {
              'zone' :{
                  required: true
              }
          },
          errorPlacement: function (error, element) {
              //error.insertBefore(element);
              error.insertAfter(element.closest('div'));
          },
          /*submitHandler: function (form) { // for demo
              alert('valid form');
              return false;
          }//
      });

    }
);*/