#!/usr/bin/env python3

import luotettavuus_lah as luotto
import socket as s
import virtsoketti as v
import sys
import time


def lopeta():
    '''Tulostaa virheilmoituksen ja lopettaa ohjelman suorituksen.'''
    sys.exit('Virhe: {}.'.format(sys.exc_info()[1]))

    
def main():
    '''Pääohjelma.'''
    palvelin = 'localhost'
    portti = 9999
    vastott = (palvelin, portti)
    osoiteperhe = s.AF_INET  # IPv4.
    sokettityyppi = s.SOCK_DGRAM  # UDP-soketti.

    try:
        # soketti = s.socket(osoiteperhe, sokettityyppi)
        soketti = v.Virtuaalisoketti(osoiteperhe, sokettityyppi)
        # Virtuaalisoketin attribuuttien säätö.
        soketti.tn_pudotus = .0
        soketti.tn_viive = .0
        soketti.tn_virhe = .0
        soketti.viive_ala = 1
        soketti.viive_yla = 3
                               
    except:
        lopeta()

    # Luodaan luotettavuuskerros-olio.
    puskurin_koko = 256  # Sama kuin ohjevideossa.
    luottokrs = luotto.Luottolahettaja(soketti, puskurin_koko, vastott)
    luottokrs.aloita()

    print('Tämä on lähettäjäsovellus.' +\
          '\nLähetysikkunan koko on {}.'.format(luottokrs.ikkuna) +\
          '\nKun annat lähetettävän merkkijonon, välilyönneillä erotetut ' +\
          'kokonaisuudet lähetetään eri paketteina.' +\
          '\nPaina Ctrl-C lopettaaksesi.\n')

    odotusaika = 0.5  # Jos luotettavuuskerros on ruuhkautunut, odotetaan
                      # tämän verran.
    # Silmukka, jossa kysytään lähetettävää ja lähetetään.
    while True:
        try:
            lahteva = input('Anna lähetettävä teksti: ')
            osat = lahteva.split()
            # Välitetään osa kerrallaan luotettavuuskerrokselle.
            for osa in osat:
                # Silmukka, jossa lähetetään. Jos lähettäminen
                # ei onnistu, odotetaan niin kauan, että se
                # onnistuu.
                print('Yritetään lähettää "{}".'.format(osa))
                while True:
                    # Lähetetään, jos luottokerros ei ole ruuhkautunut.
                    if luottokrs.voiko_lahettaa():
                        print('Lähetetään "{}".'.format(osa))
                        luottokrs.laheta_sr(osa)
                        break
                    # Muussa tapauksessa odotetaan.
                    else:
                        print('Ei voida lähettää, odotetaan...')
                        time.sleep(odotusaika)
        except KeyboardInterrupt:  # Käyttäjä painoi Ctrl-C.
            # Käydään luottokerroksen ajastimet läpi. Jos ajastin ei ole None,
            # kutsutaan sen cancel-metodia, ts. lopetetaan säikeen suoritus.
            for ajastin in luottokrs.ajastimet:
                if ajastin:
                    ajastin.cancel()
            # Lopetetaan säie, joka kuuntelee tulevia kuittauksia:
            luottokrs.loppu = True
            break
        except:  # Jokin muu meni pieleen.
            for ajastin in luottokrs.ajastimet:
                if ajastin:
                    ajastin.cancel()
            luottokrs.loppu = True
            lopeta()

    soketti.close()
    input('\n------------' +\
          '\nSoketti suljettu.' +\
          '\nPaina Enter.')


main()    
