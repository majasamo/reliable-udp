#!/usr/bin/env python3

import math


class Luottokerros:
    '''Luotettavuuskerros.

    Luottokerros vastaa pakettien lähettämisestä ja vastaanottamisesta
    luotettavan tiedonsiirron periaatteita noudattaen.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    # Tässä toteutuksessa on tarkoitus mallintaa tilakonetta Kurosen &
    # Rossin kirjan hengessä. Siksi tilat on pyritty nimeämään samoin kuin
    # em. teoksessa, vaikkakin suomen ja englannin sekamelska voi vaikuttaa
    # epäasialliselta tai koomiselta.
    #
    # Vastaanottajan mahdolliset tilat.
    #   'wait_0'   # Odotetaan pakettia 0.
    #   'wait_1'   # Odotetaan pakettia 1.
    #
    # Lähettäjän mahdolliset tilat.
    #   'wait_call0'  # Odotetaan lähetettävää viestiä nro 0.
    #   'wait_ack0'   # Odotetaan paketin nro 0 kuittausta.
    #   'wait_call1'  # Odotetaan lähetettävää viestiä nro 1.
    #   'wait_ack1'   # Odotetaan paketin nro 1 kuittausta.
    
    def __init__(self, soketti, puskurin_koko):
        # Koska sekä vastaanottaja että lähettäjä luovat oman Luottokerros-
        # olionsa, ei ole järkevää asettaa ensimmäistä tilaa vielä tässä.
        # Tila asetetaan metodissa lahett_aseta_alkutila() tai
        # vastott_aseta_alkutila().
        self.tila = None
                             
        self.soketti = soketti
        self.puskurin_koko = puskurin_koko
        self.rek = 0  # Siirtorekisterin sisältö.


    ############################################################
    # Sekä lähettäjän että vastaanottajan tarvitsemat metodit. #
    ############################################################
        
    def laheta(self, lahteva, vastott):
        '''Bittijonomuotoisen datan lähetys.'''
        self.soketti.sendto(lahteva, (vastott[0], vastott[1]))        
    

    def laheta_mjono(self, sekvno, lahteva, vastott):
        '''Paketoi merkkijonomuotoisen datan oikeaan kehysrakenteeseen
        ja lähettää paketin.
        '''
        lahteva = self.valm_paketti(sekvno, lahteva)
        self.laheta(lahteva, vastott)

        
    def valm_paketti(self, sekvno, lahteva):
        '''Valmistelee paketin: lahteva koodataan ja muodostetaan
        kehysrakenteen muotoinen paketti: itse viesti keskelle,
        alkuun sekvenssinumero, loppuun tarkistussumma.
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
        nro = sekvno.to_bytes(length=1, byteorder='big')        
        lahteva_numerollinen = nro + lahteva
        tark = self.laske_tark(lahteva_numerollinen)
        #
        # Sitten liitetään numero, itse viesti ja sekvenssinumerollisesta
        # paketista laskettu tarkistussumma yhteen.
        lahteva = nro + lahteva + tark
        # Välitetään paketti.
        return lahteva


    def pura(self, paketti):
        '''Palauttaa sekvenssinumeron ja datakentän dekoodattuina.'''
        sekvno = paketti[0]  # Kokonaisluku, ei tarvitse enää dekoodata.
        data = paketti[1:-1]  # Bittijono, pitää dekoodata.
        data = data.decode('utf8', errors='ignore')
        return (sekvno, data)
                
        
    #############################################
    # Lähettäjän (asiakkaan) käyttämät metodit. #
    #############################################

    def lahett_aseta_alkutila(self):
        '''Asettaa lähettäjälle alkutilan 'wait_call0'.'''
        self.tila = 'wait_call0'
        
    
    def lahett_tilakone(self, mjono, vastott):
        '''Lähettäjän tilakone. Huolehtii annetun merkkijonon mjono
        lähettämisestä (ja lähettäjän tilojen päivittämisestä). Metodin 
        suoritus päättyy, kun lähettäjä siirtyy tilaan 'wait_call0' tai
        'wait_call1'.
        '''
        while True:
            if self.tila == 'wait_call0':
                self.laheta_mjono(0, mjono, vastott)
                self.tila = 'wait_ack0'
                continue
            elif self.tila == 'wait_ack0':
                if self.odota_kuittaus(0):
                    self.tila = 'wait_call1'
                    return
                else:
                    self.laheta_mjono(0, mjono, vastott)
                    continue
            elif self.tila == 'wait_call1':
                self.laheta_mjono(1, mjono, vastott)
                self.tila = 'wait_ack1'
                continue
            elif self.tila == 'wait_ack1':
                if self.odota_kuittaus(1):
                    self.tila = 'wait_call0'
                    return
                else:
                    self.laheta_mjono(1, mjono, vastott)
                    continue
            else:  # Tämän ei pitäisi koskaan tapahtua.
                raise Exception('Sovellus siirtyi tuntemattomaan tilaan {}'.\
                            format(self.tila))
                    
        
    def odota_kuittaus(self, odotettu_sekvno):
        '''Palauttaa True, jos virtuaalisoketilta tuli virheetön 
        ja oikealla sekvenssinumerolla varustettu kuittaus, 
        muuten False.
        '''
        kuittaus, _ = self.soketti.recvfrom(self.puskurin_koko)
        # Jos kuittauksessa on bittivirhe, palautetaan false.
        kuittaus_ok = self.tarkasta(kuittaus)
        sekvno, kuittaus_teksti = self.pura(kuittaus)

        # Toimitaan tilanteen mukaan:
        if not kuittaus_ok:
            print('Palvelimelta tuli bittivirheellinen kuittaus: {}. '.\
                  format(kuittaus_teksti) +\
                  'Lähetetään uudestaan.\n')
            return False
        elif kuittaus_teksti == 'ACK' and sekvno == odotettu_sekvno:
            print('Palvelimelta tuli kuittaus, jossa ' +\
                  'on oikea sekvenssinumero.\n')
            return True
        elif kuittaus_teksti == 'ACK' and sekvno != odotettu_sekvno:
            print('Palvelimelta tuli kuittaus, jossa ' +\
                  'on väärä sekvenssinumero. Lähetetään uudestaan.\n')
            return False
        else:  # Tarkistussumma oikein mutta data jotain muuta kuin
               # 'ACK'. Näin ei pitäisi periaatteessa käydä.
            print('Palvelimelta tuli epäselvä vastaus. Lähetetään uudestaan.\n')
            return False
            
    
    #################################################
    # Vastaanottajan (palvelimen) käyttämät metodit #
    #################################################

    def vastott_aseta_alkutila(self):
        '''Asettaa vastaanottajalle alkutilan 'wait_0'.'''
        self.tila = 'wait_0'


    def vastott_tilakone(self):
        '''Vastaanottajan tilakone. Huolehtii paketin vastaanottamisesta
        (ja tilojen päivittämisestä). Metodi palauttaa paketin datakentän
        merkkijonomuodossa, kun tila muuttuu.
        '''
        while True:
            if self.tila == 'wait_0':
                onnistuiko, data = self.vastaanota(0)
                if onnistuiko:
                    self.tila = 'wait_1'
                    return data
                else:
                    continue
            elif self.tila == 'wait_1':
                onnistuiko, data = self.vastaanota(1)
                if onnistuiko:
                    self.tila = 'wait_0'
                    return data
                else:
                    continue
            else:  # Tämän ei pitäisi koskaan tapahtua.
                raise Exception('Sovellus siirtyi tuntemattomaan tilaan {}'.\
                                format(self.tila))


    def vastaanota(self, odotettu_sekvno):
        '''Paketin vastaanotto ja kuittausten lähetys. Jos saapunut paketti
        on bittivirheetön ja
        siinä on oikea sekvénssinumero, paluuarvo on (True, data) missä data
        on paketin datakentän arvo merkkijonona. Muussa tapauksessa paluuarvo
        on (False, None).
        '''
        saapunut, lahettaja = self.soketti.recvfrom(self.puskurin_koko)
        crc_ok = self.tarkasta(saapunut)
        sekvno, data = self.pura(saapunut)
        # Lasketaan valmiiksi myös toinen sekvenssinumero.
        toinen_sekvnro = (odotettu_sekvno + 1) % 2
        
        # Kolme vaihtoehtoa:
        #
        # 1. ei bittivirhettä ja oikea sekvenssinumero.
        # Lähetetään ACK oikealla numerolla.
        if crc_ok and sekvno == odotettu_sekvno:
            print('Vastaanotettu virheetön paketti, jossa oikea ' +\
                  'sekvenssinumero.\n')
            self.laheta_mjono(odotettu_sekvno, 'ACK', lahettaja)
            return (True, data)
        # 2. ei bittivirhettä mutta väärä sekvenssinumero.
        # Lähetetään ACK väärällä numerolla.
        elif crc_ok and sekvno != odotettu_sekvno:
            print('Vastaanotettu virheetön paketti, jossa väärä ' +\
                  'sekvenssinumero.\n')
            self.laheta_mjono(toinen_sekvnro, 'ACK', lahettaja)
            return (False, None)
        # 3. bittivirhe. Lähetetään ACK väärällä numerolla.
        # Tämähän on oikeastaan sama kuin edellinen kohta, mutta
        # pidetään tämä testauksen ja ehkä selkeydenkin vuoksi
        # erillään.
        else:
            print('Vastaanotettu bittivirheellinen paketti.\n')
            self.laheta_mjono(toinen_sekvnro, 'ACK', lahettaja)
            return (False, None)

        
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
        
    
