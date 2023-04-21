Tässä vaiheessa tarvittiin lähettäjän puolella nähdäkseni jo
jonkinlaista rinnakkaisuutta, ja tämän toteutin säikeillä. Yksi säie
ottaa vastaan ja käsittelee kuittauksia. Toinen säie lähettää
paketteja ja luo tarvittaessa ajastinsäikeen. Kun tapahtuu ajastimen
aikakatkaisu, luodaan ja käynnistetään uusi ajastinsäie. Samalla
suoritetaan kuittaamattomien pakettien uudelleenlähetys.

Ohjelma tekee aika paljon testitulostuksia. Siksi tiedostoissa
lahett_app.py ja vastott_app.py on todennäköisyydet kaikille
virtuaalisoketin aiheuttamille virheille ja viiveelle laitettu
nollaksi. Ohjelmaa kannattaa nimittäin ensin testata ilman virheitä ja
viivettä, jotta tottuu tulostuksiin. Sen jälkeen virheparametrit voi
säätää haluamikseen. Varsinkin lähettävä sovellus voi tuntua
sekavalta, koska se saattaa kysyä lähetettävää ja heti perään tulostaa
ruudulle tietoja prosessin etenemisestä, mutta tätä sekavuutta ei
oikein voi välttää, kun kyseessä ei kuitenkaan ole graafinen
käyttöliittymä. Olen joka tapauksessa sitä mieltä, että runsas
tulostaminen on testaamisen kannalta hyvä asia tai ainakin pienempi
paha.