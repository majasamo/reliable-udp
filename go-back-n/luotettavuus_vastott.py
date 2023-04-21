#!/usr/bin/env python3

import luotettavuus


class Luottovastaanottaja(luotettavuus.Luottokerros):
    '''Vastaanottajan luotettavuuskerros.

    Luottovastaanottaja vastaa pakettien vastaanottamisesta
    Go back N -algoritmin mukaisesti.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    
    def __init__(self, soketti, puskurin_koko):
        super().__init__(soketti, puskurin_koko)
        self.odotettu_sekvno = 1  # Tämä on aluksi 1. Jos nimittäin
                                  # ensimmäinen paketti on virheellinen,
                                  # lähetetään kuittaus, jossa on
                                  # sekvenssinumero 0.
        self.max = 16  # Sekvenssinumeroiden lukumäärä. Suurin sekvenssinumero
                       # on siis self.max - 1. Tässä voisi olla 256, mutta
                       # käytetään pienempää numeroa harjoituksen vuoksi,
                       # jotta nähdään, miten modulo-aritmetiikka toimii.
        self.kuittaus = self.valm_paketti(0, 'ACK')

        
    def ota_vastaan(self):
        '''Palauttaa viestin merkkijonona, jos viestillä on oikea
        sekvenssinumero eikä siinä ole bittivirheitä. Muussa tapauksessa
        paluuarvo on None.'''
        saapunut, lahettaja = self.soketti.recvfrom(self.puskurin_koko)
        crc_ok = self.tarkasta(saapunut)
        sekvno, data = self.pura(saapunut)
        if crc_ok and sekvno == self.odotettu_sekvno:
            self.kuittaus = self.valm_paketti(self.odotettu_sekvno, \
                                              'ACK')
            print('(Vastaanotettu virheetön paketti, jossa odotettu ' +\
                  'sekvenssinumero.)')
            self.kuittaa(lahettaja)
            self.odotettu_sekvno = (self.odotettu_sekvno + 1) % self.max
            return data
        else:
            print('(Vastaanotettu virheellinen paketti: bittivirhe tai ' +\
                  'väärä sekvenssinumero.)')
            self.kuittaa(lahettaja)
            return None

        
    def kuittaa(self, vastott):
        '''Lähettää kuittauksen. Metodin kutsujan on huolehdittava
        siitä, että attribuuttina oleva kuittaus on päivitetty.'''
        self.laheta(self.kuittaus, vastott)
        print('(Lähetetty kuittaus, sekvenssinumero {}.)'.\
              format(self.kuittaus[0]))
