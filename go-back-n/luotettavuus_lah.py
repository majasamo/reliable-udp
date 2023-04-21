#!/usr/bin/env python3

import luotettavuus
import socket as s
import threading as thrd


class Luottolahettaja(luotettavuus.Luottokerros):
    '''Lähettäjän luotettavuuskerros.

    Luottolahettaja vastaa pakettien lähettämisestä Go back N -algoritmia
    käyttäen.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    
    def __init__(self, soketti, puskurin_koko, vastott):
        super().__init__(soketti, puskurin_koko)
        # Koska vastaanottaja on koko ajan sama, se voi
        # ihan hyvin olla attribuutti.
        self.vastott = vastott
        
        self.lukuaika = 0.5  # Aika, joka kertoo, kuinka kauan kuittausta
                             # yritetään lukea.
        # Varsinaiset GBN-muuttujat:
        self.ikkuna = 4   # Lähetysikkunan koko.
        self.vanhin = 1  # Vanhin kuittaamaton sekvenssinumero. Tämä voi olla
                         # välillä [0, self.max-1]. 
        self.seur = 1   # Seuraavan lähetettävän paketin sekvenssinumero. Tämä
                        # voi olla välillä [0, self.max-1]. Tämä on aluksi
                        # 1, koska jos ensimmäinen lähetetty paketti
                        # menee perille virheellisenä, vastaanottaja
                        # voi ilmoittaa asiasta lähettämällä kuittauksen,
                        # jonka sekvenssinumero on 0.
        self.max = 16  # Sekvenssinumeroiden lukumäärä. Suurin sekvenssinumero
                       # on siis self.max - 1. Tässä voisi olla 256, mutta
                       # käytetään pienempää numeroa harjoituksen vuoksi,
                       # jotta nähdään, miten modulo-aritmetiikka toimii.

        # Kun paketti lähtee, se tallentuu tähän listaan, jotta se olisi
        # helpompi lähettää uudelleen. Indeksi vastaa sekvenssinumeroa.
        self.kuittaamattomat = self.max*[None]

        # Ajastimen aikakatkaisun jälkeen tapahtuu uudelleenlähetys.
        self.ajastin = None
        self.aika = 2.0

        # Lukitusta käytetään, jotta yksi säie ei muuttaisi attribuutteja
        # sillä välin kun toinen säie lukee niitä.
        self.lukko = thrd.Lock()

        # Metodi odota_kuittauksia() lopetetaan asettamalla tämän
        # attribuutin arvoksi True. Tämä tapahtuu, kun lahett_app-ohjelman
        # main()-metodi käsittelee KeyboardInterruptia tai muuta poikkeusta.
        # Ratkaisu on kömpelö, mutta esim. poikkeuskäsittelyn lisääminen
        # odota_kuittauksia()-metodiin ei toimi halutulla tavalla.
        self.loppu = False

        
    def aloita(self):
        '''Alkaa kuunnella sokettia kuittausten varalta.
        Huom.! Tätä metodia on tarkoitus kutsua vain yhden kerran.'''
        # Luodaan ja käynnistetään säie, joka odottaa kuittauksia.
        odotus = thrd.Thread(target=self.odota_kuittauksia)
        odotus.start()


    def odota_kuittauksia(self):
        kuittaus = ''
        self.soketti.settimeout(self.lukuaika)
        # Yritetään lukea sokettia. Sokettia yritetään lukea vain tietyn aikaa
        # kerrallaan ja suorituskertojen välissä tarkastetaan self_loppu.
        # Kun self_loppu == True, metodin suoritus päättyy. Näin tehdään,
        # koska metodin suoritusta (ja sitä kautta säikeen suoritusta)
        # ei saada muuten KeyboardInterruptilla lopetetuksi.
        while not self.loppu:
            try:
                kuittaus, _ = self.soketti.recvfrom(self.puskurin_koko)
                self.kasittele_kuittaus(kuittaus)
            except s.timeout:
                pass
            # lahett_appin main()-metodi on saattanut jo sulkea soketin.
            # Siinä tapauksessa pitäisi olla self.loppu == True.
            except:   
                continue


    def kasittele_kuittaus(self, kuittaus):
        '''Lukee tavujonomuotoisen kuittauksen, tarkastaa sen ja
        huolehtii kuittauksen aiheuttamista jatkotoimista.'''
        # Jos kuittauksessa on bittivirhe, ei jatketa.
        if not self.tarkasta(kuittaus):
            print('(Bittivirheellinen kuittaus.)')
            return

        # Muuten:
        # Kuittaus tulkitaan kumulatiivisena, joten vanhimman
        # kuittaamattoman paketin numero päivittyy.
        sekvno, _ = self.pura(kuittaus)
        print('(Vastaanotettiin bittivirheetön kuittaus, jonka ' +\
              'sekvenssinumero on {}.)'.format(sekvno))
        
        with self.lukko:
            self.vanhin = (sekvno + 1) % self.max

            # Jos kaikki on jo kuitattu, pysäytetään ajastin. Muussa
            # tapauksessa käynnistetään se uudelleen.
        
            if self.vanhin == self.seur:
                self.ajastin.cancel()
            else:
                self.kaynnista_ajastin()

            
    def voiko_lahettaa(self):
        '''Palauttaa tiedon, onko lähettäminen mahdollista.'''
        # Periaatteessa vertailuoperaatio on
        # self.seur < self.vanhin + self.ikkuna, mutta
        # modulo-aritmetiikka on otettava huomioon.
        with self.lukko:
            if self.seur < self.vanhin:
                return self.seur + self.max < self.vanhin + self.ikkuna
            else:
                return self.seur < self.vanhin + self.ikkuna
        
    
    def laheta_gbn(self, mjono):
        '''Merkkijonon lähettäminen Go-back-N-protokollan mukaisesti.'''
        # Ennen lähettämistä varaudutaan mahdollisiin uudelleenlähetyksiin:
        # valmistellaan paketti (sekvenssinumero ja tarkistussumma mukaan)
        # ja lisätään se kuittaamattomien joukkoon.
        with self.lukko:
            lahteva = self.valm_paketti(self.seur, mjono)
            self.kuittaamattomat[self.seur] = lahteva
            # Sitten lähetetään.
            self.laheta(lahteva, self.vastott)
            print('(Lähetetty, sekvenssinumero {}.)\n'.format(self.seur))
            self.seur = (self.seur + 1) % self.max

            # Jos juuri lähetetty paketti on samalla vanhin kuittaamaton
            # paketti, käynnistetään ajastin.
            if self.vanhin == self.seur-1:
                self.kaynnista_ajastin()

        
    def kaynnista_ajastin(self):
        '''Nollaa ja käynnistää ajastimen uudestaan.'''
        # Otetaan huomioon, että ensimmäisellä kerralla ajastin on None,
        # jolloin sillä ei ole cancel()-metodia.
        if self.ajastin:
            self.ajastin.cancel()
        self.ajastin = thrd.Timer(self.aika, function=self.timeout)
        self.ajastin.start()

        
    def timeout(self):
        '''Ajastimen aikakatkaisu: ajastin uudelleen käyntiin
        ja kuittaamattomien pakettien uudelleenlähetys.'''
        print('(Aikakatkaisu!)')
        self.kaynnista_ajastin()
        self.laheta_uudestaan()

    
    def laheta_uudestaan(self):
        '''Lähettää kuittaamattomat paketit uudestaan.'''
        # Määritetään indeksien joukko. Periaatteessa kyseessä on
        # välillä [self.vanhin, self.seur[ olevien kokonaislukujen
        # joukko, mutta lisäksi täytyy ottaa huomioon modulo-
        # aritmetiikka.
        with self.lukko:
            if self.seur < self.vanhin:
                indeksit = list(range(self.vanhin, self.max))  # Alkuosa.
                # Liitetään loput (nollasta alkavat) yksitellen.
                for x in range(0, self.seur):
                    indeksit.append(x)    
            else:
                indeksit = list(range(self.vanhin, self.seur))

        print('(Lähetetään uudelleen paketit {}.)'.format(indeksit))
        for i in indeksit:
            self.laheta(self.kuittaamattomat[i], self.vastott)    
