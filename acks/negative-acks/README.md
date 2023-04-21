Kurose–Rossissa ei tietääkseni tämäntyyppistä protokollaa ole, joten
suunnittelin itse: Lähettäjä lähettää paketin ja odottaa mahdollista
negatiivista kuittausta. Jos kuittausta ei tule tietyn ajan kuluessa,
se olettaa, että kaikki on kunnossa. (Odottamisessa ei ole kysymys
virtuaalisoketin aiheuttamasta viiveestä, sillä sitä ei ole. Sen
sijaan odottamalla varmistetaan, että vastaanottaja on ehtinyt purkaa
paketin ja tarvittaessa lähettää negatiivisen kuittauksen.)
Vastaanottaja puolestaan tarkastaa paketin ja lähettää negatiivisen
kuittauksen, jos paketissa on bittivirhe. Jos bittivirhettä ei ole, se
ei lähetä mitään. Näin voidaan tehdä, koska oletuksena on, että
paketit eivät katoa eikä viivettä ole. Paketti sisältää datan ja CRC 8
-tarkistussumman mutta ei sekvenssinumeroa. Negatiivinen kuittaus
puolestaan sisältää vain yhden tavun verran nollia. Itse asiassa on
aivan sama, mitä kuittaus sisältää, sillä lähettäjä olettaa, että jos
vastaanottajalta tulee jotain, kyseessä on negatiivinen
kuittaus. Lähettäjän on siis turhaa tutkia kuittauksen sisältöä
esim. bittivirheiden varalta.