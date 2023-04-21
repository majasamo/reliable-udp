#!/usr/bin/env python3

import luotettavuus
import socket as s


class Luottolahettaja(luotettavuus.Luottokerros):
    '''Lähettäjän luotettavuuskerros.

    Luottolahettaja vastaa pakettien lähettämisestä luotettavan tiedonsiirron
    periaatteita noudattaen.

    Toiminta vastaa Kurosen & Rossin protokollaa rdt3.0.

    Bittivirheiden tarkastamisessa käytetään CRC 8 -algoritmia.
    Polynomina on x**8 + x**3 + x**2 + x + 1, 
    bittimuodossa 100000111.
    '''

    # Lähettäjän mahdolliset tilat.
    #   'wait_call0'  # Odotetaan lähetettävää viestiä nro 0.
    #   'wait_ack0'   # Odotetaan paketin nro 0 kuittausta.
    #   'wait_call1'  # Odotetaan lähetettävää viestiä nro 1.
    #   'wait_ack1'   # Odotetaan paketin nro 1 kuittausta.
    
    def __init__(self, soketti, puskurin_koko):
        super().__init__(soketti, puskurin_koko)
        self.tila = None
        self.odotusaika = 0.6  # Aika, joka kertoo, kuinka kauan kuittausta
                               # odotetaan.


    def aseta_alkutila(self):
        '''Asettaa lähettäjälle alkutilan 'wait_call0'.'''
        self.tila = 'wait_call0'
        
    
    def tilakone(self, mjono, vastott):
        '''Lähettäjän tilakone. Huolehtii annetun merkkijonon mjono
        lähettämisestä (ja lähettäjän tilojen päivittämisestä). Metodin 
        suoritus päättyy, kun lähettäjä siirtyy tilaan 'wait_call0' tai
        'wait_call1'.
        '''
        while True:
            if self.tila == 'wait_call0':
                self.wait_call(0, mjono, vastott)
                continue
            elif self.tila == 'wait_ack0':
                if self.wait_ack(0, mjono, vastott):
                    return
                else:
                    continue
            elif self.tila == 'wait_call1':
                self.wait_call(1, mjono, vastott)
                continue
            elif self.tila == 'wait_ack1':
                if self.wait_ack(1, mjono, vastott):
                    return
                else:
                    continue
            else:  # Tämän ei pitäisi koskaan tapahtua.
                raise Exception('Sovellus siirtyi tuntemattomaan tilaan {}'.\
                            format(self.tila))

            
    def wait_call(self, sekvno, mjono, vastott):
        '''wait_call-tilojen toteutus.'''
        self.laheta_mjono(sekvno, mjono, vastott)
        self.tila = 'wait_ack{}'.format(sekvno)
        return

    
    def wait_ack(self, sekvno, mjono, vastott):
        '''wait_ack-tilojen toteutus. Palauttaa True, jos virtuaalisoketilta
        tuli virheetön ja oikealla sekvenssinumerolla varustettu kuittaus, 
        muuten False. Jos tapahtuu ajastimen aikakatkaisu, palautetaan 
        False. '''
        self.soketti.settimeout(self.odotusaika)

        # Yritetään lukea soketin sisältö.
        kuittaus_ok = False
        try:
            while not kuittaus_ok:
                kuittaus_ok = self.lue_kuittaus(sekvno)
            # Jos silmukka päättyy, vaihdetaan tilaa ja palautetaan
            # True.
            toinen_nro = (sekvno + 1) % 2  # Toinen sekvenssinumero.
            self.tila = 'wait_call{}'.format(toinen_nro)
            self.soketti.settimeout(None)
            return True
        except s.timeout:
            # Lähetetään uudelleen, pysytään samassa tilassa ja
            # palautetaan False.
            print('Ajastimen aikakatkaisu. Lähetetään uudestaan.\n')
            self.laheta_mjono(sekvno, mjono, vastott)
            self.soketti.settimeout(None)
            return False

        
    def lue_kuittaus(self, odotettu_sekvno):
        '''Palauttaa True, jos virtuaalisoketilta tuli virheetön 
        ja oikealla sekvenssinumerolla varustettu kuittaus, 
        muuten False.
        '''
        kuittaus, _ = self.soketti.recvfrom(self.puskurin_koko)
        kuittaus_ok = self.tarkasta(kuittaus)
        sekvno, kuittaus_teksti = self.pura(kuittaus)

        # Kaksi vaihtoehtoa:
        if kuittaus_ok and kuittaus_teksti == 'ACK' and\
           sekvno == odotettu_sekvno:
            print('Palvelimelta tuli kuittaus, jossa ' +\
                  'on oikea sekvenssinumero.\n')
            return True
        else:
            print('Palvelimelta tuli jokin muu kuin odotettu kuittaus. ' +\
                  'Ei aiheuta toimenpiteitä.\n')
            return False
            
    
