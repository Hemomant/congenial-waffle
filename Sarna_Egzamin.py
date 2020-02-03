# -*- coding: cp1250 -*-

#import bibliotek
import arcpy
from math import sqrt, pi
#nadpisywanie warstwy wyjściowej
arcpy.env.overwriteOutput = True

#***Główna funcja programu***
def Budynki():
    try:
        print('Program wczytał biblioteki, teraz wczytuje i przetwarza warstwe')
        #wczytanie warstwy wyjściowej
        #layer = arcpy.GetParameterAsText(0)
        layer = arcpy.MakeFeatureLayer_management(r".\Dane.shp", "dane")
        #funkcja klucz
        simplify(layer) 
        print('koniec pracy')
    except Exception, err:
        arcpy.AddError("Blad Budynki")
        arcpy.AddError(sys.exc_traceback.tb_lineno)
        arcpy.AddError(err.message)
    finally: pass


    #***Funkcja wybierajaca badany budynek i zliczajaca wiercholki sasiednie i sciany sasiednie***
def simplify(layer):
    try:
        #Utworzenie kursora czytania budynkow
        kursor_czytania = arcpy.da.SearchCursor(layer, ["SHAPE@"])
        idbudynku = arcpy.da.SearchCursor(layer, ['OBJECTID'])
        #tolerancja uproszczenia dla 180
        tolerancja = input('podaj tolerancje katowa (zalecane blisko 0, gdyz wartosci sa z Acos): ')
        
        #Czytanie id
        bid = []
        for i in idbudynku:
            bid.append(i[0])
            
        #parametr ilosci odcinanych punktow
        k = input('podaj ilosc omijanych wierzcholkow: ')
        #k = 1
        
        #tablica robocza
        redukowane = []
        InOut = []
        Idtable = []
        Idstable = []
        budyneczek = -1 
        #Wybranie i uproszczenie badanego budynku
        for bud in kursor_czytania:
            print ('Przetwarzany budynek : {}'.format(budyneczek+2))
            budyneczek += 1 
            punkty = read2(bud[0])
            idskolejne = 0



            #Petla z głównym warunkiem uproszczenia - szukanie siecznej spelniajacej warunki
            while (len(punkty) > 4 and len(punkty)-2*k > 1):
                print ('Iteracja : {}'.format(idskolejne+1))
                #tworzenie zmiennych do pojedynczego budynku
                punkty2 = []
                bud180 = []
                sciany = []
                wyciete = []
                uproszczone = []
                poly1 = []
                poly2 = []
                #zmienne dla siecznych
                #warstwasiecznych = []
                mindlu = -1
                poczodc = -1
                konodc = -1   
                    
                #uproszczenie budynkow 180 stopni
                for p0 in range(1, len(punkty)):
                    punkty2.append([punkty[p0][0],punkty[p0][1]])                
                for p0 in range(0, len(punkty2)):
                    #wektory
                    CL = [punkty2[p0-2][0]-punkty2[p0-1][0],punkty2[p0-2][1]-punkty2[p0-1][1]]
                    CP = [punkty2[p0][0]-punkty2[p0-1][0],punkty2[p0][1]-punkty2[p0-1][1]]
                    CPCL = CP[0]*CL[0]+CP[1]*CL[1]
                    CLD = sqrt(CP[0]*CP[0]+CP[1]*CP[1])
                    CPD = sqrt(CL[0]*CL[0]+CL[1]*CL[1])
                    if CLD*CPD != 0:
                        ALFA = (CPCL/(CLD*CPD))
                    else:
                        ALFA = 0

                    #sprawdzenie czy sciana jest prosta
                    if ALFA > -1+tolerancja:
                        bud180.append([punkty2[p0-1][0],punkty2[p0-1][1]])
                        sciany.append([punkty2[p0-1][0],punkty2[p0-1][1]])

                #Utworzenie warstwy scian do analizy przeciecia oraz In_Out
                sciany.append([bud180[0][0],bud180[0][1]])
                sciany = arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in sciany]))

                #Główny warunek dla uproszczonych 180
                if (len(bud180) > 4 and len(bud180)-2*k > 1):
                    #zatrzymajka dla petli while
                    stop = 0

                    #Uproszczenie siecznymi
                    for p0 in range(0, len(bud180)-k-1):
                        #Zasięgi tworzenia siecznych
                        if p0 < k:
                            zasieg = len(bud180)-k+p0
                        else:
                            zasieg = len(bud180)

                        #tworzenie siecznych                   
                        for ids in range(1+k+p0, zasieg):
                            siecznatest = [arcpy.Point(bud180[p0][0], bud180[p0][1]), arcpy.Point(bud180[ids][0], bud180[ids][1])]
                            siecznatest = arcpy.Polyline(arcpy.Array([siecznatest]))
                            #warstwasiecznych.append(siecznatest)
                            
                            #liczenie odleglosci
                            odl = sqrt((bud180[p0][0]-bud180[ids][0])**2+(bud180[p0][1]-bud180[ids][1])**2)

                            #szukanie najkrotszej siecznej
                            if p0 == 0 and ids == 1+k+p0 and not siecznatest.crosses(sciany):
                                mindlu = odl
                                poczodc = p0
                                konodc = ids
                            else:
                                if (odl < mindlu and not sciany.crosses(siecznatest)) or mindlu == -1:
                                    mindlu = odl
                                    poczodc = p0
                                    konodc = ids                                    
                #zatrzymanie petli
                if poczodc == -1 or konodc == -1:
                    break

                #Uproszczenie wybrana sieczna
                for nowe in range(0, len(bud180)):
                    if (nowe == poczodc or nowe == konodc):
                        wyciete.append([bud180[nowe][0],bud180[nowe][1]])
                        uproszczone.append([bud180[nowe][0],bud180[nowe][1]])
                    elif (nowe > poczodc and nowe < konodc):
                        wyciete.append([bud180[nowe][0],bud180[nowe][1]])             
                    else:
                        uproszczone.append([bud180[nowe][0],bud180[nowe][1]])
                        
                #sprawdzenie czy na zewnatrz
                if siecznatest.within(sciany):
                    InOut.append(0)
                else:
                    InOut.append(1)

                Idstable.append(idskolejne)
                idskolejne += 1
                Idtable.append(bid[budyneczek])


                #tworzenie warstwy uproszczoej i odcietej        
                poly1.append(wyciete) 
                poly2.append(uproszczone)
                poly1[0].append([wyciete[0][0],wyciete[0][1]])
                poly2[0].append([uproszczone[0][0],uproszczone[0][1]])

                #Sprawdzenie warunku powierzchniowego - nie wiemy w ktora strone jest rysowany poligon wiec moglibysmy "odciac" wieksza czesc!
                polyg1 = arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in poly1[0]]))
                polyg2 = arcpy.Polygon(arcpy.Array([arcpy.Point(*coords) for coords in poly2[0]]))                
                area1 = polyg1.area
                area2 = polyg2.area            
                if area2 >= area1:
                    punkty = poly2[0]
                    redukowane.append(polyg1)
                else:
                    punkty = poly1[0]
                    redukowane.append(polyg2)
                    
                #arcpy.AddMessage([area1, area2])

        arcpy.CopyFeatures_management(redukowane, ".\wynikowe.shp")
        wynik = arcpy.MakeFeatureLayer_management(r".\wynikowe.shp", "wynik")
        #arcpy.AddMessage(redukowane)
        
        #Kursor pola
        addfield("Id", wynik)
        addfield("Id_s", wynik)
        addfield("In_Out", wynik)
        uid = arcpy.da.UpdateCursor(wynik, "Id")
        uids = arcpy.da.UpdateCursor(wynik, "Id_s")
        uio = arcpy.da.UpdateCursor(wynik, "In_Out")
        
        #Dodanie wartosci do pola 
        i = 0
        for row in uid:
            row[0] = Idtable[i]
            i = i+1
            uid.updateRow(row)
            
        #Dodanie wartosci do pola 
        i = 0    
        for row in uids:
            row[0] = Idstable[i]
            i = i+1
            uids.updateRow(row)

        #Dodanie wartosci do pola 
        i = 0    
        for row in uio:
            row[0] = InOut[i]
            i = i+1
            uio.updateRow(row)
            
        #arcpy.AddMessage(wynik)    
        #uproszczonawarstwa = layer.difference(redukowane)
        
    except Exception, err:
        arcpy.AddError("Blad funkcji badbud")
        arcpy.AddError(sys.exc_traceback.tb_lineno)
        arcpy.AddError(err.message)
    finally: pass

#***Funkcja odczytująca geometrie pojedynczych punktow***
def read2(geometria):
    try:
        listatmp=[]
        for part in geometria:
            for pnt in part:
                if pnt:
                    listatmp.append([pnt.X, pnt.Y])
                    
        del(geometria, part, pnt)  
    except Exception, err:
            arcpy.AddError("blad read2")
            arcpy.AddError(sys.exc_traceback.tb_lineno)
            arcpy.AddError(err.message)
    finally: return listatmp

#***Funkcja dodajaca pola do tabeli atrybutow***    
def addfield (field_name, layer):
    try:
        if not field_name in [f.name for f in arcpy.ListFields(layer)]:
            arcpy.AddField_management(layer, field_name, "SHORT")

        del(field_name,layer)  
    except Exception, err:
            arcpy.AddError("blad addfield")
            arcpy.AddError(sys.exc_traceback.tb_lineno)
            arcpy.AddError(err.message)
    finally: pass

if __name__== '__main__':
    Budynki()
