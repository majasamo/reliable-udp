#!/usr/bin/env python3

import luotettavuus


class Luottovastaanottaja(luotettavuus.Luottokerros):
    '''Vastaanottajan luotettavuuskerros.

    Luottovastaanottaja vastaa pakettien vastaanottamisesta
    selective repeat -algoritmin mukaisesti.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    
    def __init__(self, soketti, puskurin_koko):
        super().__init__(soketti, puskurin_koko)
        self.kuittaukset = self.max*[None]
        self.puskuri = self.max*[None]
        # self.vanhin,
        # self.ikkuna ja
        # self.max peritään kantaluokasta.


    def ota_vastaan(self):
        '''Palauttaa viestin merkkijonona, jos viestillä on oikea
        sekvenssinumero eikä siinä ole bittivirheitä. Muussa tapauksessa
        paluuarvo on None.'''
        self.tulosta_ikkuna()
        saapunut, lahettaja = self.soketti.recvfrom(self.puskurin_koko)
        crc_ok = self.tarkasta(saapunut)
        sekvno, data = self.pura(saapunut)

        # Lasketaan valmiiksi tiedot siitä, onko sekvenssinumero ikkunassa.
        #
        # Onko numero vastaanottoikkunan sisällä?
        ikkunaehto1 = self.onko_ikkunassa(self.vanhin,
                                          self.vanhin+self.ikkuna,
                                          self.max,
                                          sekvno)
        # Onko numero ikkunan [self.vanhin-self.ikkuna, self.vanhin[
        # sisällä? Alaraja self.vanhin-self.ikkuna voi kuitenkin olla
        # negatiivinen eikä metodi onko_ikkunassa() osaa ottaa tätä huomioon.
        alaraja = self.vanhin-self.ikkuna if self.vanhin >= self.ikkuna\
                  else self.vanhin-self.ikkuna+self.max
        ikkunaehto2 = self.onko_ikkunassa(alaraja, self.vanhin, self.max,
                                          sekvno)

        # Kolme vaihtoehtoa:
        #
        # Ei bittivirhettä, sekvenssinumero vastaanottoikkunan sisällä:
        # kuitataan, tallennetaan data puskuriin ja palautetaan
        # puskurin sisältöä, jos sekvno on yhtä suuri kuin self.vanhin.
        if (crc_ok and ikkunaehto1):
            self.kuittaukset[sekvno] = self.valm_paketti(sekvno, 'ACK')
            print('(Vastaanotettu virheetön paketti, jonka ' +\
                  'sekvenssinumero on ikkunan sisällä.)')
            self.kuittaa(sekvno, lahettaja)
            self.puskuri[sekvno] = data
            if sekvno == self.vanhin:
                return self.palauta_puskurista()
            else:
                return None
        # Ei bittivrirhettä, mutta täytyy kuitata: kuitataan.
        elif (crc_ok and ikkunaehto2):
            print('Vastaanotettu virheetön paketti, jonka sekvenssinumero '+\
                    'ei ole ikkunan sisällä mutta joka vaatii kuittaamista.')
            self.kuittaa(sekvno, lahettaja)
            return None
        # Muut vaihtoehdot: ei tehdä mitään.
        else:
            print('(Vastaanotettu virheellinen paketti: bittivirhe tai ' +\
                  'väärä sekvenssinumero.)')
            return None

        
    def kuittaa(self, sekvno, vastott):
        '''Lähettää kuittauksen.'''
        self.laheta(self.kuittaukset[sekvno], vastott)
        print('(Lähetetty kuittaus, sekvenssinumero {}.)'.format(sekvno))


    def palauta_puskurista(self):
        '''Palauttaa vastaanottopuskurista oikeassa järjestyksessä olevien
        merkkijonojen listan alkaen indeksistä self.vanhin. Palautettavat
        merkkijonot poistetaan puskurista. Lisäksi metodi
        huolehtii self.vanhin-attribuutin päivittämisestä.'''
        palautus = []
        while self.puskuri[self.vanhin]:
            palautus.append(self.puskuri[self.vanhin])
            self.puskuri[self.vanhin] = None
            self.vanhin = (self.vanhin + 1) % self.max
        return palautus
