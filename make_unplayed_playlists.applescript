on addTracks(plName, theList)
	tell application "Music"
		if exists user playlist plName then delete user playlist plName
		set pl to make new user playlist with properties {name:plName}
		set missing to ""
		set added to 0
		repeat with x in theList
			set n to item 1 of x
			set a to item 2 of x
			try
				set hits to (every track of library playlist 1 whose name is n and artist is a)
				if (count of hits) > 0 then
					duplicate (item 1 of hits) to pl
					set added to added + 1
				else
					set missing to missing & linefeed & "  not found: " & a & " - " & n
				end if
			on error e
				set missing to missing & linefeed & "  error (" & e & "): " & a & " - " & n
			end try
		end repeat
	end tell
	return plName & ": added " & added & " of " & (count of theList) & missing
end addTracks

tell application "Music"
	if exists user playlist "Unplayed Favorites" then delete user playlist "Unplayed Favorites"
end tell

set r1 to addTracks("Unplayed: Rock and Folk", {{"Mr. Soul", "Buffalo Springfield"}, ¬
  {"Incense and Peppermint", "Strawberry Alarm Clock"}, ¬
  {"A Well Respected Man", "The Kinks"}, ¬
  {"No Matter What (2010 Remaster)", "Badfinger"}, ¬
  {"Here Comes That Rainy Day Feeling Again", "The Fortunes"}, ¬
  {"Let It Ride", "McGuinness Flint"}, ¬
  {"Only Love Can Break Your Heart", "Neil Young"}, ¬
  {"Hold Your Head Up", "Argent"}, ¬
  {"All the Young Dudes", "Mott the Hoople"}, ¬
  {"The Pusher", "Steppenwolf"}, ¬
  {"The Low Spark of High-Heeled Boys", "Traffic"}, ¬
  {"Alison", "Elvis Costello"}, ¬
  {"Werewolves of London", "Warren Zevon"}, ¬
  {"Lawyers, Guns and Money", "Warren Zevon"}, ¬
  {"You Better You Bet", "The Who"}, ¬
  {"Sensation", "Bryan Ferry"}, ¬
  {"Don't Dream It's Over", "Crowded House"}, ¬
  {"Can't Hardly Wait", "The Replacements"}, ¬
  {"Whistling In the Dark", "They Might Be Giants"}, ¬
  {"If I Can’t Be Your Lover (I Won’t Be Your Friend)", "Ted Lucas"}, ¬
  {"Strange Mysterious Sounds", "The Spike Drivers"}, ¬
  {"SPECIAL WEAKNESS", "Nirosta Steel"}, ¬
  {"Frail In The Mind", "cutters"}, ¬
  {"The Weak", "Iceage"}, ¬
  {"Music Is My Hot, Hot Sex", "CSS"}, ¬
  {"F**k the Pain Away", "Peaches"}, ¬
  {"Down In It", "Nine Inch Nails"}, ¬
  {"Big Man with a Gun", "Nine Inch Nails"}, ¬
  {"Endgames", "Godflesh"}, ¬
  {"Sifting", "Chat Pile"}, ¬
  {"Closure", "Opeth"}, ¬
  {"Mother (2019 Remaster)", "Goldie"}})
set r2 to addTracks("Unplayed: Rap", {{"Positive Contact (Charlie Clouser Remix) [Bonus Track]", "Deltron 3030"}, ¬
  {"No Rest for the Wicked", "Cypress Hill"}, ¬
  {"Fakin' The Funk (Sound Track Version)", "Main Source"}, ¬
  {"Green Island", "Redman"}, ¬
  {"Ice Cream (feat. Ghostface Killah, Method Man & Cappadonna)", "Raekwon"}, ¬
  {"Ain't No Thang", "Outkast"}, ¬
  {"Love U", "2nd II None"}, ¬
  {"D-Boyz Got Love For Me (feat. E-40)", "Spice 1"}, ¬
  {"Can't C Me", "2Pac"}, ¬
  {"Hip-Hop", "Dead Prez"}, ¬
  {"The Pistol (feat. Maintain of Illegal Tendencies)", "Dead Prez"}, ¬
  {"Fiesta (feat. Kid Capri)", "Noreaga"}, ¬
  {"Put Ya Hands Up (Explicit)", "Jadakiss"}, ¬
  {"X Gon' Give It To Ya", "DMX"}, ¬
  {"Let a N*gga Know", "Saigon"}, ¬
  {"Watch Yo Enemies (feat. Magic)", "C-Murder"}, ¬
  {"We Can Dance", "Silkk the Shocker"}, ¬
  {"Bounce Dat Azz", "Master P, Gangsta T, King George & Silkk the Shocker"}, ¬
  {"Everyday (feat. T.C., Lil’ Marquice, Taz, Shasta & Cresia)", "Lil' Flip"}, ¬
  {"Just Like Ous", "Three 6 Mafia"}, ¬
  {"Choose U", "Project Pat"}, ¬
  {"Ballers", "Project Pat"}, ¬
  {"Stay Fly", "Three 6 Mafia"}, ¬
  {"Baby Mamma", "Boosie Badazz & Webbie"}, ¬
  {"What Happened To That Boy (feat. Clipse)", "Baby"}, ¬
  {"When the Last Time", "Clipse"}, ¬
  {"Go DJ", "Lil Wayne"}, ¬
  {"Get High Rule The World", "Lil Wayne"}, ¬
  {"Stupid Wild (feat. Lil Wayne, Cam'ron)", "Gucci Mane"}, ¬
  {"Mean Mug (feat. 50 Cent)", "Soulja Boy Tell 'Em & 50 Cent"}, ¬
  {"Incredible", "Main Attrakionz"}, ¬
  {"Nothin Gonna Change", "Main Attrakionz"}, ¬
  {"Rap Junkies", "Main Attrakionz"}, ¬
  {"Grief", "Earl Sweatshirt"}, ¬
  {"Tread Lightly", "Armand Hammer"}, ¬
  {"Unknown Species", "Kurious"}, ¬
  {"Barry Gibb", "Kurious"}, ¬
  {"Hell on Earth, Pt. 2 (feat. Benny the Butcher & Conway the Machine)", "Westside Gunn"}, ¬
  {"Who Dat Boy (feat. A$AP Rocky)", "Tyler, The Creator"}, ¬
  {"2Pac", "Future"}, ¬
  {"The Percocet & Stripper Joint", "Future"}, ¬
  {"Real Ni**a", "21 Savage & Metro Boomin"}, ¬
  {"Still Serving", "21 Savage, Offset & Metro Boomin"}, ¬
  {"Spicy (feat. Fivio Foreign & A$AP Ferg)", "Nas"}, ¬
  {"F**k the Party up (feat. Rio Da Yung Og)", "Drakeo the Ruler & JoogSzn"}, ¬
  {"Spend Some Money (feat. Ace Cino)", "Damedot"}, ¬
  {"Toot That Booty", "Raheem The Dream"}, ¬
  {"Went Legit", "G Herbo"}, ¬
  {"Heating Up", "YN Jay"}, ¬
  {"Zoo Life Blessing", "BabyChiefDoit"}, ¬
  {"pajama", "Jace!"}})
return r1 & linefeed & r2
