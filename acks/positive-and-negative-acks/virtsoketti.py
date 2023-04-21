#!/usr/bin/env python3

import math
import random as rand
import socket as s
import time


class Virtuaalisoketti(s.socket):
    '''Virtuaalinen soketti simuloi ei-luotettavaa tiedonsiirtoa.

    Virtuaalisoketti on toteutettu perimällä se normaalista soketista.
    Uudestaan on toteutettu (init-metodin lisäksi) ainoastaan recvfrom-metodi.
    Näin ollen virtuaalista sokettia käytettäessä on tarkoitus kutsua vain
    edellä mainittua metodia, sillä muut soketin metodit toimivat kuten
    tavallisessa soketissa.
    '''
    tn_pudotus = .0  # Millä todennäköisyydellä paketti pudotetaan?

    tn_viive = .0  # Millä todennäköisyydellä tulee viivettä?
    viive_ala = 0  # Viiveen alaraja
    viive_yla = 2  # ja yläraja sekunteina.

    tn_virhe = .7  # Bittivirheen todennäköisyys. 

    
    def __init__(self, osoiteperhe, sokettityyppi):
        super().__init__(osoiteperhe, sokettityyppi)

        
    def recvfrom(self, puskurin_koko):
        '''Toimii kuten tavallisen soketin recvfrom-metodi, mutta mukana on
        myös ei-luotettavan tiedonsiirron simulointi.'''
        while True:
            saapunut = super().recvfrom(puskurin_koko)
            
            if rand.random() < self.tn_pudotus:
                print('Paketti katosi.')  # Testaamista varten.
            else:
                self.viive()
                saapunut = self.virhe(saapunut)
                return saapunut

            
    def viive(self):
        '''Keskeyttää satunnaisesti ohjelman suorituksen satunnaisen
        pitkäksi ajaksi.'''
        if rand.random() < self.tn_viive:
            viive = self.viive_ala +\
                    (self.viive_yla - self.viive_ala) * rand.random()
            print('Viive: {} s'.format(viive))  # Testaamista varten.
            time.sleep(viive)
        return

    
    def virhe(self, saapunut):
        '''Tekee tietyllä todennäköisyydellä saapuneeseen pakettiin
        satunnaisen bittivirheen.'''
        paketti, lahettaja = saapunut
        if not paketti:                  # Tässä vaiheessa ei täysin tyhjää
            return (paketti, lahettaja)  # pakettia pitäisi saapua (vähintään
                                         # sekvenssinumero ja tarkistussumma
                                         # mukana), mutta olkoon tämä tässä
                                         # varmuuden vuoksi.
        if rand.random() < self.tn_virhe:
            paketti = self.bittivirhe(paketti)
        return (paketti, lahettaja)


    def bittivirhe(self, data):
        '''Tekee datan satunnaiseen kohtaan yhden bitin virheen.'''
        # HUOM: Alla oleva toteutus on sikäli vajavainen, että se ei ota
        # huomioon etunollia. Jos on. esim lähetetty tyhjä merkkijono,
        # jonka mukana on sekvenssinumero 0 ja tarkistussumma 0, se tulkitaan
        # alla yhden bitin mittaiseksi nollaksi. Kun siihen tehdään virhe, se
        # muuttuu ykköseksi. Jotta kehysrakenne säilyisi oikeanlaisena,
        # bittijonoksi muunnettaessa ykkösen eteen lisätään niin monta
        # etunollaa, että kaksi tavua tulee täyteen. Tässä olisi siis 16 eri
        # mahdollisuutta bittivirheelle, mutta bittivirhe tulee aina vähiten
        # merkitsevään kohtaan.
        #
        # Bittioperaatioita varten muunnetaan tavujono (bytes)
        # kokonaisluluvuksi. Valinnalla 'big' eniten merkitsevä
        # bitti tulee vasemmalle.
        tavupituus = len(data)  # Varmistetaan, että tavupituus säilyy samana.
        alkup = int.from_bytes(data, byteorder='big')

        # Valitaan satunnainen kohta, johon bittivirhe tulee.
        pituus = alkup.bit_length()
        pituus = max(1, pituus)  # Jos alkup on 0, sen bittipituus on 0.
                                 # Kuitenkin tämä 0 voidaan ymmärtää yhtenä
                                 # bittinä, johon voi tehdä myös virheen.
        paikka = rand.randint(0, pituus-1)

        # Etsitään käännettävä bitti ja käännetään se.
        bitti = int(bin(alkup)[-(paikka+1)])  # Koska bin-funktion paluuarvo on
                                              # muotoa '0b101010', etsittyä
                                              # bittiä haetaan loppupäästä.
        vastabitti = int(not bitti)  # Käännetty bitti.


        # Muodostetaan virheellinen data.
        maski = 1 << paikka  # Ykkönen halutussa kohdassa, muut nollia.
        virheellinen = (alkup & (~maski)) | (vastabitti << paikka)

        # Testaus:
        print('Virtuaalisoketti generoi bittivirheen.')
        # print('Bittivirhe. Alkuperäinen:\n  {}, \nvirheellinen:\n  {}, '.\
        #        format(bin(alkup), bin(virheellinen)) +\
        #       'virhe bitissä nro {}.'.format(paikka))

        return virheellinen.to_bytes(length=tavupituus, byteorder='big')
