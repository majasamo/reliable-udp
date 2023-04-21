#!/usr/bin/env python3


class Luottokerros:
    '''Luotettavuuskerros.

    Luottokerros vastaa pakettien lähettämisestä ja vastaanottamisesta
    luotettavan tiedonsiirron periaatteita noudattaen. Vain negatiivisia 
    kuittauksia käytetään.
    
    TOIMINTA
    Vastaanottajalla on vain yksi tila. Lähettäjällä puolestaan on seuraavat
    tilat:
      'wait_call': odotetaan lähetettävää viestiä
      'wait_nak': odotetaan mahdollista negatiivista kuittausta.

    Kun lähettäjä saa lähetettävää, se lähettää ja siirtyy tilaan 'wait_nak'.
    Tilassa 'wait_nak' se odottaa tietyn ajan (oletusarvoisesti 0.5 s)
    mahdollista negatiivista kuittausta. Jos negatiivista kuittausta ei
    tule, oletetaan, että vastaanottaja on saanut paketin, jossa ei
    ole bittivirheitä.

    Vastaanottaja puolestaan tarkastaa saamansa paketin ja lähettää
    negatiivisen kuittauksen (NAK), jos paketissa on bittivirhe. Muussa
    tapauksessa kuittausta ei lähetetä.

    Lähetettävät paketit sisältävät varsinaisen datan ja yhden tavun
    mittaisen CRC 8 -kentän. Sekvenssinumeroa ei käytetä. Negatiiviset 
    kuittaukset puolestaan sisältävät vain yhden tavun verran nollia.
    NAK-viesteihinkin voi tietysti tulla bittivirheitä, mutta lähettäjä
    ei tarkasta NAK-viestejä mitenkään. Ideana on, että jos vastaanottajalta
    tulee jokin paketti, se on aina negatiivinen kuittaus.

    BITIVIRHEET
    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    def __init__(self, soketti, puskurin_koko):
        # Koska sekä vastaanottaja että lähettäjä luovat oman Luottokerros-
        # olionsa, ei ole järkevää asettaa ensimmäistä tilaa vielä tässä.
        # Tila asetetaan metodissa lahett_aseta_alkutila() tai
        # vastott_aseta_alkutila().
        self.tila = None
                             
        self.soketti = soketti
        self.puskurin_koko = puskurin_koko
        self.rek = 0  # Siirtorekisterin sisältö.

        self.nak_odotusaika = 0.5  # Aika, jonka lähettäjä odottaa
                                   # mahdollista negatiivista kuittausta.
        

    ############################################################
    # Sekä lähettäjän että vastaanottajan tarvitsemat metodit. #
    ############################################################
        
    def laheta(self, lahteva, vastott):
        '''Bittijonomuotoisen datan lähetys.'''
        self.soketti.sendto(lahteva, (vastott[0], vastott[1]))        
                    
        
    #############################################
    # Lähettäjän (asiakkaan) käyttämät metodit. #
    #############################################

    def lahett_aseta_alkutila(self):
        '''Asettaa lähettäjälle alkutilan 'wait_call'.'''
        self.tila = 'wait_call'
        
    
    def lahett_tilakone(self, mjono, vastott):
        '''Lähettäjän tilakone. Huolehtii annetun merkkijonon mjono
        lähettämisestä (ja lähettäjän tilojen päivittämisestä). Metodin 
        suoritus päättyy, kun lähettäjä siirtyy tilaan 'wait_call'.
        '''
        while True:
            if self.tila == 'wait_call':
                self.laheta_mjono(mjono, vastott)
                self.tila = 'wait_nak'
                continue
            elif self.tila == 'wait_nak':
                if self.tuliko_nak():
                    self.laheta_mjono(mjono, vastott)
                    self.tila = 'wait_nak'
                    continue
                else:
                    self.tila = 'wait_call'
                    return
            else:  # Tämän ei pitäisi koskaan tapahtua.
                raise Exception('Sovellus siirtyi tuntemattomaan tilaan {}'.\
                            format(self.tila))
                    
        
    def tuliko_nak(self):
        '''Palauttaa True, jos virtuaalisoketilta tuli 
        negatiivinen kuittaus, muuten false.
        '''
        # Asetetaan soketti timeout-moodiin.
        self.soketti.settimeout(self.nak_odotusaika)
        kuittaus = False
        # Yritetään lukea soketti. Jos lukeminen ei onnistu
        # odotusajan kuluessa, keskeytetään. Kummassakin tapauksessa
        # soketti palautetaan blocking-moodiin.
        try:
            kuittaus, _ = self.soketti.recvfrom(self.puskurin_koko)
            print('Palvelimelta tuli negatiivinen kuittaus.\n')
            self.soketti.settimeout(None)
            return True
        except:
            self.soketti.settimeout(None)
            return False

        
    def laheta_mjono(self,lahteva, vastott):
        '''Paketoi merkkijonomuotoisen datan oikeaan kehysrakenteeseen
        ja lähettää paketin.
        '''
        lahteva = self.valm_paketti(lahteva)
        self.laheta(lahteva, vastott)

        
    def valm_paketti(self, lahteva):
        '''Valmistelee paketin: lahteva koodataan ja muodostetaan
        kehysrakenteen muotoinen paketti: itse viesti alkuun,
        loppuun tarkistussumma.
        '''
        # Itse data ja tarkistussumma.
        lahteva = lahteva.encode('utf8')
        tark = self.laske_tark(lahteva)
        # Kasataan:
        lahteva = lahteva + tark
        # Välitetään paketti.
        return lahteva
        
    
    #################################################
    # Vastaanottajan (palvelimen) käyttämät metodit #
    #################################################

    def vastott_tilakone(self):
        '''Vastaanottajan tilakone. Huolehtii paketin vastaanottamisesta.
        Jos paketti läpäisee tarkastuksen, siinä oleva datakenttä palautetaan
        merkkijonomuodossa.
        '''
        while True:
            onnistuiko, data = self.vastaanota()
            if onnistuiko:
                return data
            else:
                continue

            
    def pura(self, paketti):
        '''Palauttaa datakentän dekoodattuna.'''
        data = paketti[0:-1]  # Bittijono, pitää dekoodata.
        data = data.decode('utf8', errors='ignore')
        return data
            

    def vastaanota(self):
        '''Paketin vastaanotto ja kuittausten lähetys. Jos saapunut paketti
        on bittivirheetön, paluuarvo on (True, data) missä data
        on paketin datakentän arvo merkkijonona. Muussa tapauksessa paluuarvo
        on (False, None).
        '''
        saapunut, lahettaja = self.soketti.recvfrom(self.puskurin_koko)
        crc_ok = self.tarkasta(saapunut)
        data = self.pura(saapunut)
        
        # Kaksi vaihtoehtoa:
        #
        # 1. ei bittivirhettä.
        # Otetaan vastaan, ei lähetetä kuittausta.
        if crc_ok:
            print('Vastaanotettu virheetön paketti.\n')
            return (True, data)
        # 2. bittivirhe.
        # Lähetetään NAK.
        else:
            print('Vastaanotettu bittivirheellinen paketti.\n')
            self.laheta_nak(lahettaja)
            return (False, None)

        
    def laheta_nak(self, vastott):
        '''Lähettää negatiivisen kuittauksen.'''
        lahetettava = 0
        lahetettava = lahetettava.to_bytes(length=1, byteorder='big')
        self.laheta(lahetettava, vastott)
        
        
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
        
    
