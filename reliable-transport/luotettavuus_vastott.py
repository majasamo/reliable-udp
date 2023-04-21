#!/usr/bin/env python3

import luotettavuus


class Luottovastaanottaja(luotettavuus.Luottokerros):
    '''Vastaanottajan luotettavuuskerros.

    Luottovastaanottaja vastaa pakettien vastaanottamisesta luotettavan 
    tiedonsiirron periaatteita noudattaen.

    Toiminta vastaa Kurosen & Rossin protokollaa rdt3.0.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    # Vastaanottajan mahdolliset tilat.
    #   'wait_0'   # Odotetaan pakettia 0.
    #   'wait_1'   # Odotetaan pakettia 1.

    def __init__(self, soketti, puskurin_koko):
        super().__init__(soketti, puskurin_koko)
        self.tila = None


    def aseta_alkutila(self):
        '''Asettaa vastaanottajalle alkutilan 'wait_0'.'''
        self.tila = 'wait_0'


    def tilakone(self):
        '''Vastaanottajan tilakone. Huolehtii paketin vastaanottamisesta
        (ja tilojen päivittämisestä). Metodi palauttaa paketin datakentän
        merkkijonomuodossa, kun tila muuttuu.
        '''
        while True:
            if self.tila == 'wait_0':
                onnistuiko, data = self.wait(0)
                if onnistuiko:
                    self.tila = 'wait_1'
                    return data
                else:
                    continue
            elif self.tila == 'wait_1':
                onnistuiko, data = self.wait(1)
                if onnistuiko:
                    self.tila = 'wait_0'
                    return data
                else:
                    continue
            else:  # Tämän ei pitäisi koskaan tapahtua.
                raise Exception('Sovellus siirtyi tuntemattomaan tilaan {}'.\
                                format(self.tila))

            
            
    def wait(self, odotettu_sekvno):
        '''wait-tilojen totetus. Paketin vastaanotto ja kuittausten lähetys.
        Jos saapunut paketti on bittivirheetön ja
        siinä on oikea sekvenssinumero, paluuarvo on (True, data) missä data
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
