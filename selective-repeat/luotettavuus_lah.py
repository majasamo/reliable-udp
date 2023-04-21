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
                             
        # self.vanhin,
        # self.ikkuna ja
        # self.max peritään kantaluokasta.
        self.seur = 0   # Seuraavan lähetettävän paketin sekvenssinumero. Tämä
                        # voi olla välillä [0, self.max-1]. 

        # Kun paketti lähtee, se tallentuu tähän listaan, jotta se olisi
        # helpompi lähettää uudelleen. Indeksi vastaa sekvenssinumeroa.
        # Kun tietyn paketin kuittaus saapuu, paketin kohdalle
        # tallennetaan None.
        self.kuittaamattomat = self.max*[None]

        # Jokaista lähetettyä pakettia vastaa ajastin. Ajastimen
        # indeksi on sama kuin sekvenssinumero.
        self.ajastimet = self.max*[None]
        self.aika = 2.0

        # Lukitusta käytetään, jotta toinen säie ei muuttaisi attribuutteja
        # sillä välin kun jokin toinen lukee niitä.
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
        sekvno, _ = self.pura(kuittaus)
        print('(Vastaanotettiin bittivirheetön kuittaus, jonka ' +\
              'sekvenssinumero on {}.)'.format(sekvno))

        # Jos sekvenssinumero ei ole lähetysikkunan sisällä, ei tehdä mitään.
        # Muussa tapauksessa toimitaan seuraavasti:
        with self.lukko:
            if self.onko_ikkunassa(self.vanhin, self.vanhin+self.ikkuna,
                                   self.max, sekvno):
                # Pysäytetään ajastin ja kirjataan paketti kuitatuksi.
                self.ajastimet[sekvno].cancel()
                self.kuittaamattomat[sekvno] = None
                
                # Tarvittaessa päivitetään self.vanhin.
                if sekvno == self.vanhin:
                    # Kasvatetaan self.vanhin-attribuuttia yhdellä niin
                    # kauan, että sen kohdalla on kuittaamattomissa jotain
                    # muuta kuin None TAI self.vanhin on yhtä suuri kuin
                    # self.seur.
                    while ((not self.kuittaamattomat[self.vanhin]) and
                           (self.vanhin != self.seur)):
                        self.vanhin = (self.vanhin + 1) % self.max

                # Tulostetaan vielä tilanne.
                self.tulosta_ikkuna()

                        
    def voiko_lahettaa(self):
        '''Palauttaa tiedon, onko lähettäminen mahdollista.'''
        with self.lukko:
            self.tulosta_ikkuna()
            return self.onko_ikkunassa(self.vanhin, self.vanhin+self.ikkuna,
                                       self.max, self.seur)
        
    
    def laheta_sr(self, mjono):
        '''Merkkijonon lähettäminen selective repeat -protokollan mukaisesti.'''
        # Ennen lähettämistä varaudutaan mahdollisiin uudelleenlähetyksiin:
        # valmistellaan paketti (sekvenssinumero ja tarkistussumma mukaan)
        # ja lisätään se kuittaamattomien joukkoon.
        with self.lukko:
            lahteva = self.valm_paketti(self.seur, mjono)
            self.kuittaamattomat[self.seur] = lahteva
            # Lähetetään ja käynnistetään ajastin.
            self.laheta(lahteva, self.vastott)
            self.kaynnista_ajastin(self.seur)
            print('(Lähetetty, sekvenssinumero {}.)\n'.format(self.seur))
            self.seur = (self.seur + 1) % self.max

        
    def kaynnista_ajastin(self, indeksi):
        '''Nollaa ja käynnistää ajastimen uudestaan.'''
        # Otetaan huomioon, että ensimmäisellä kerralla ajastin on None,
        # jolloin sillä ei ole cancel()-metodia.
        ajastin = self.ajastimet[indeksi]
        if ajastin:
            ajastin.cancel()
        # Tehdään uusi ajastin ja käynnistetään se.
        ajastin = thrd.Timer(self.aika, function=self.timeout, args=[indeksi])
        self.ajastimet[indeksi] = ajastin
        ajastin.start()

        
    def timeout(self, indeksi):
        '''Ajastimen aikakatkaisu: ajastin uudelleen käyntiin
        ja paketin uudelleenlähetys.'''
        print('(Aikakatkaisu!)')
        self.kaynnista_ajastin(indeksi)
        self.laheta_uudestaan(indeksi)

    
    def laheta_uudestaan(self, indeksi):
        '''Lähettää indeksillä varustetun paketin uudestaan.'''
        print('(Lähetetään uudelleen paketti {}.)'.format(indeksi))
        self.laheta(self.kuittaamattomat[indeksi], self.vastott)    
