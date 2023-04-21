#!/usr/bin/env python3

import math


class Luottokerros:
    '''Luotettavuuskerros.

    Luottokerros vastaa pakettien lähettämisestä ja vastaanottamisesta
    luotettavan tiedonsiirron periaatteita noudattaen.

    Bittivirheiden tarkastamisessa käytettä CRC 8 algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    
    def __init__(self, soketti, puskurin_koko):
        self.soketti = soketti
        self.puskurin_koko = puskurin_koko
        self.sekv = 0  # Sekvenssinumero. Lähettäjällä lähetettävän paketin
                       # numero, vastaanottajalla se numero, jota
                       # tulevassa paketissa odotetaan.
        self.rek = 0  # Siirtorekisterin sisältö.

        
    def vaihda_sekv(self):
        '''Vaihtaa sekvenssinumeron.'''
        self.sekv = (self.sekv + 1) % 2

        
    #############################################
    # Lähettäjän (asiakkaan) käyttämät metodit. #
    #############################################

    def laheta(self, lahteva, vastott):
        '''Bittijonomuotoisen datan lähetys.'''
        self.soketti.sendto(lahteva, (vastott[0], vastott[1]))        
    

    def laheta_mjono(self, lahteva, vastott):
        '''Vastaa merkkijonomuotoisen datan lähetyksestä, tarvittavat
        uudelleenlähetykset mukaan luettuna.
        '''
        lahteva = self.valm_paketti(lahteva)

        # Lähetetään niin monta kertaa uudestaan, että tulee oikea kuittaus.
        onnistuiko = False
        while not onnistuiko:
            self.laheta(lahteva, vastott)
            onnistuiko = self.odota_kuittaus()
        self.vaihda_sekv()


    def odota_kuittaus(self):
        '''Palauttaa True, jos virtuaalisoketilta tuli virheetön ACK, 
        muuten False.
        '''
        kuittaus, _ = self.soketti.recvfrom(self.puskurin_koko)
        # Jos kuittauksessa on bittivirhe, palautetaan false.
        kuittaus_ok = self.tarkasta(kuittaus)
        kuittaus_teksti = kuittaus[0:-1].decode('utf8', errors='ignore')

        # Toimitaan tilanteen mukaan:
        if not kuittaus_ok:
            print('Palvelimelta tuli bittivirheellinen kuittaus: {}. '.\
                  format(kuittaus_teksti) +\
                  'Lähetetään uudestaan.')
            return False
        elif kuittaus_teksti == 'NAK':
            print('Palvelimelta tuli negatiinen kuittaus. ' +\
                  'Lähetetään uudestaan.')
            return False
        elif kuittaus_teksti == 'ACK':
            print('Palvelimelta tuli positiivinen kuittaus.')
            return True
        else:  # Tarkistussumma oikein mutta data jotain muuta kuin
               # 'ACK' tai 'NAK'. Näin ei pitäisi periaatteessa käydä.
            print('Palvelimelta tuli epäselvä vastaus. Lähetetään uudestaan.')
            return False
            

    def valm_paketti(self, lahteva):
        '''Valmistelee paketin: lahteva koodataan ja muodostetaan
        kehysrakenteen muotoinen paketti: itse viesti keskelle,
        alkuun vuoronumero, loppuun tarkistussumma.
        '''
        # Kasataan paketti: keskelle itse viesti, alkuun sekvenssinumero,
        # loppuun tarkistussumma.
        #
        # Käytännön ongelma on kuitenkin, että jos sekvenssinumero on 0,
        # niin se häviää, kun bittijono muunnetaan kokonaisluvuksi.
        # Se pitää siis lisätä pakettiin uudestaan. Toisaalta pitää
        # varoa, ettei pakettiin lisätä kahta ykköstä.
        #
        # Muodostetaan sekvenssinumerollinen paketti ja lasketaan
        # siitä tarkistussumma:
        lahteva = lahteva.encode('utf8')
        nro = self.sekv.to_bytes(length=1, byteorder='big')        
        lahteva_numerollinen = nro + lahteva
        tark = self.laske_tark(lahteva_numerollinen)
        #
        # Sitten liitetään numero, itse viesti ja sekvenssinumerollisesta
        # paketista laskettu tarkistussumma yhteen.
        lahteva = nro + lahteva + tark
        # Välitetään paketti.
        return lahteva

    
    #################################################
    # Vastaanottajan (palvelimen) käyttämät metodit #
    #################################################

    def vastaanota(self):
        '''Paketin vastaanotto.'''
        while True:
            saapunut, lahettaja = self.soketti.recvfrom(self.puskurin_koko)
            crc_ok = self.tarkasta(saapunut)
            sekvno, data = self.pura(saapunut)
            # Kolme vaihtoehtoa:
            #
            # 1. ei bittivirhettä ja oikea sekvenssinumero.
            # Lähetetään ACK, muutetaan sekvenssinumeroa ja
            # välitetään data eteenpäin.
            if crc_ok and sekvno == self.sekv:
                self.laheta_kuittaus(True, lahettaja)
                self.vaihda_sekv()
                print('Vastaanotettu virheetön paketti, jossa oikea ' +\
                      'sekvenssinumero.\n')
                return data
            # 2. ei bittivirhettä mutta väärä sekvenssinumero.
            # Lähetetään ACK ja jäädään odottamaan.
            elif crc_ok and sekvno != self.sekv:
                self.laheta_kuittaus(True, lahettaja)
                print('Vastaanotettu virheetön paketti, jossa väärä ' +\
                      'sekvenssinumero.\n')
            # 3. bittivirhe.
            # Lähetetään NAK ja jäädään odottamaan.
            else:
                print('Vastaanotettu bittivirheellinen paketti.\n')
                self.laheta_kuittaus(False, lahettaja)

                
    def pura(self, paketti):
        '''Palauttaa sekvenssinumeron ja datakentän dekoodattuina.'''
        sekvno = paketti[0]  # Kokonaisluku, ei tarvitse enää dekoodata.
        data = paketti[1:-1]  # Bittijono, pitää dekoodata.
        data = data.decode('utf8', errors='ignore')
        return (sekvno, data)
                
                
    def laheta_kuittaus(self, kuittaus, vastott):
        '''Jos kuittaus on True, lähetetään positiivinen kuittaus, 
        muussa tapauksessa negatiivinen kuittaus.
        '''
        viesti = ''
        if kuittaus:
            viesti = 'ACK' 
        else:
            viesti = 'NAK'
        viesti = viesti.encode('utf8')
        tark = self.laske_tark(viesti)
        viesti = viesti + tark
        self.laheta(viesti, vastott)

        
    ###############################
    # CRC 8:aan liittyvät metodit #
    ###############################

    def tarkasta(self, data, testaus=False):
        '''Suorittaa CRC 8 -tarkastuksen vastaanotetulle datalle.'''
        data = int.from_bytes(data, byteorder='big')
        self.crc8(data, testaus)
        return self.rek == 0
        
        
    def laske_tark(self, data, testaus=False):
        '''Palauttaa CRC 8 -tarkistussumman bittijonona.'''
        data = int.from_bytes(data, byteorder='big')
        data = data << 8  # Kahdeksan nollaa perään.
        self.crc8(data, testaus)  # Lasketaan tarkistussumma.
        return self.rek.to_bytes(length=1, byteorder='big')
        

    def crc8(self, data, testaus=False):
        '''CRC 8 -algoritmin toteutus kokonaislukumuotoiselle datalle.'''
        self.rek = 0

        # Annetaan jokainen bitti erikseen siirtorekisterille.
        pituus = data.bit_length()
        for i in range(pituus, 0, -1):
            bitti = ((1 << i-1) & data) >> i-1  # Bitti kohdassa i-1.
            self.siirtorek(bitti, testaus)
    

    def siirtorek(self, bitti, testaus):
        '''Suorittaa yhden siirtorekisterin askeleen.'''
        if testaus:
            print('Rekisteri ensin: {}\ntuleva bitti: {}'.\
                  format(bin(self.rek), bitti))

        # Bitit.
        bitti7 = (self.rek & 0b10000000) >> 7  # Bitti kohdassa 7.
        bitti1 = (self.rek & 0b10) >> 1  # Bitti kohdassa 1.
        bitti0 = self.rek & 0b1  # Bitti kohdassa 0.

        # Uudet arvot.
        bitti2 = bitti7 ^ bitti1
        bitti1 = bitti7 ^ bitti0
        bitti0 = bitti7 ^ bitti
        uudet = (bitti2 << 2) | (bitti1 << 1) | bitti0  # Yhdistelmä.

        # Laitetaan uudet arvot rekisteriin.
        self.rek = self.rek << 1  # Siirretään bittejä yksi vasemmalle.
        self.rek = self.rek & 0b11111000  # Nollataan vanhat.
        self.rek = self.rek | uudet  # Uudet arvot tilalle.

        if testaus:
            print('Rekisteri jälkeen: {}\n'.format(bin(self.rek)))
        
    
