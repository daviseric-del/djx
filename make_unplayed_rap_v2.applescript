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

return addTracks("Unplayed: Rap v2", {{"Incredible", "Main Attrakionz"}, ¬
  {"Nothin Gonna Change", "Main Attrakionz"}, ¬
  {"Rap Junkies", "Main Attrakionz"}, ¬
  {"Grief", "Earl Sweatshirt"}, ¬
  {"Tread Lightly", "Armand Hammer"}, ¬
  {"Hell on Earth, Pt. 2 (feat. Benny the Butcher & Conway the Machine)", "Westside Gunn"}, ¬
  {"Ice Cream (feat. Ghostface Killah, Method Man & Cappadonna)", "Raekwon"}, ¬
  {"Fakin' The Funk (Sound Track Version)", "Main Source"}, ¬
  {"Barry Gibb", "Kurious"}, ¬
  {"Unknown Species", "Kurious"}, ¬
  {"Green Island", "Redman"}, ¬
  {"No Rest for the Wicked", "Cypress Hill"}, ¬
  {"Positive Contact (Charlie Clouser Remix) [Bonus Track]", "Deltron 3030"}, ¬
  {"The Pistol (feat. Maintain of Illegal Tendencies)", "Dead Prez"}, ¬
  {"Let a N*gga Know", "Saigon"}, ¬
  {"Love U", "2nd II None"}, ¬
  {"D-Boyz Got Love For Me (feat. E-40)", "Spice 1"}, ¬
  {"Can't C Me", "2Pac"}, ¬
  {"F**k the Party up (feat. Rio Da Yung Og)", "Drakeo the Ruler & JoogSzn"}, ¬
  {"Hip-Hop", "Dead Prez"}, ¬
  {"Fiesta (feat. Kid Capri)", "Noreaga"}, ¬
  {"Put Ya Hands Up (Explicit)", "Jadakiss"}, ¬
  {"X Gon' Give It To Ya", "DMX"}, ¬
  {"Ain't No Thang", "Outkast"}, ¬
  {"When the Last Time", "Clipse"}, ¬
  {"What Happened To That Boy (feat. Clipse)", "Baby"}, ¬
  {"Go DJ", "Lil Wayne"}, ¬
  {"Get High Rule The World", "Lil Wayne"}, ¬
  {"Stupid Wild (feat. Lil Wayne, Cam'ron)", "Gucci Mane"}, ¬
  {"Watch Yo Enemies (feat. Magic)", "C-Murder"}, ¬
  {"We Can Dance", "Silkk the Shocker"}, ¬
  {"Everyday (feat. T.C., Lil’ Marquice, Taz, Shasta & Cresia)", "Lil' Flip"}, ¬
  {"Baby Mamma", "Boosie Badazz & Webbie"}, ¬
  {"Just Like Ous", "Three 6 Mafia"}, ¬
  {"Choose U", "Project Pat"}, ¬
  {"Ballers", "Project Pat"}, ¬
  {"Stay Fly", "Three 6 Mafia"}, ¬
  {"2Pac", "Future"}, ¬
  {"The Percocet & Stripper Joint", "Future"}, ¬
  {"Real Ni**a", "21 Savage & Metro Boomin"}, ¬
  {"Still Serving", "21 Savage, Offset & Metro Boomin"}, ¬
  {"Who Dat Boy (feat. A$AP Rocky)", "Tyler, The Creator"}, ¬
  {"Spicy (feat. Fivio Foreign & A$AP Ferg)", "Nas"}, ¬
  {"Went Legit", "G Herbo"}, ¬
  {"Mean Mug (feat. 50 Cent)", "Soulja Boy Tell 'Em & 50 Cent"}, ¬
  {"Bounce Dat Azz", "Master P, Gangsta T, King George & Silkk the Shocker"}, ¬
  {"Spend Some Money (feat. Ace Cino)", "Damedot"}, ¬
  {"Heating Up", "YN Jay"}, ¬
  {"Zoo Life Blessing", "BabyChiefDoit"}, ¬
  {"pajama", "Jace!"}, ¬
  {"Toot That Booty", "Raheem The Dream"}})
