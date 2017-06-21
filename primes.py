import tools
from enum import Flag,auto
from os.path import dirname
from functools import total_ordering

path = dirname(__file__)

def search(query):
	if query in Item: return Item[query]
	elif query in Component: return Component[query]
	elif query in Relic: return Relic[query]

def parseall():
	parseitems()
	parserelics()
	parsevault()
	parsewishlist()

def parseitems():
	file = open(path+"\prime items.txt")
	for line in file:
		line = line.strip()
		if line: parseitem(line)
	for i in Item: i.createcomponents()

def parseitem(line):
	if "=" in line:
		name, componentsubstring = line.split("=")
		componentstrings = componentsubstring.split("+")
	else:
		name = line
		componentstrings = []
	return Item(name,componentstrings)

def parserelics():
	file = open(path+"\prime relics.txt")
	tier = ""
	for line in file:
		line = line.strip()
		if line:
			if line[-1] == ":": tier = line[:-1]
			else: parserelic(line,tier)
	for i in Relic: i.createcontents()

def parserelic(line,tier):
	name, componentsubstring = line.split("=")
	componentstrings = componentsubstring.split("+")
	return Relic(tier,name,componentstrings)

def parsevault():
	file = open(path+"\prime vault.txt")
	for line in file:
		line = line.strip()
		if line: Item[line].addtovault()

def parsewishlist():
	file = open(path+"\wishlist.txt")
	for line in file:
		line = line.strip()
		if line:
			c = Component[line]
			c.flags |= Flags.wanted
			for r in c.relics: r.flags |= Flags.wanted

class Flags(Flag):
	common = auto()
	uncommon = auto()
	rare = auto()
	wanted = auto()
	vaulted = auto()

class IndexClass(type):
	def __init__(cls,name,bases,namespace):
		super().__init__(name,bases,namespace)
		cls.database = {}
	def __getitem__(cls,key): return cls.database[key]
	def __setitem__(cls,key,value): cls.database[key] = value
	def __delitem__(cls,key): del cls.database[key]
	def __contains__(cls,key): return key in cls.database
	def __iter__(cls): return iter(cls.database.values())

class Item(metaclass=IndexClass):
	vault = []
	def __init__(self,name,componentstrings):
		self.name = name
		self.componentstrings = componentstrings
		self.flags = Flags(0)
		Item[name] = self
	def createcomponents(self):
		self.components = []
		if not self.components:
			self.blueprint = Component(self)
			self.components.append(self.blueprint)
			if self.componentstrings:
				for i in self.componentstrings:
					if i[0] == "#": self.components += Item.database[i[1:]].createcomponents()
					else: self.components.append(Component(self,i))
		if Flags.vaulted in self.flags: self.addtovault()
		return self.components
	def addtovault(self):
		self.flags |= Flags.vaulted
		for i in self.components: i.addtovault()
		return self
	def __str__(self): return self.name
	__repr__ = __str__

class Component(metaclass=IndexClass):
	defaultdisplaymode = Flags.rare | Flags.wanted | Flags.vaulted
	def __init__(self,item,name=""):
		self.item = item
		self.name = name
		if name: self.fullname = item.name + " " + name
		else: self.fullname = item.name
		self.flags = Flags(0)
		self.relics = []
		self.ducats = 0
		Component[self.fullname] = self
	def addtovault(self):
		self.flags |= Flags.vaulted
		for i in self.relics: i.flags |= Flags.vaulted
		return self
	def updateducats(self):
		if self.name == "Forma": self.ducats = 0
		elif (Flags.common|Flags.uncommon) in self.flags: self.ducats = 25
		elif (Flags.uncommon|Flags.rare) in self.flags: self.ducats = 65
		elif Flags.common in self.flags: self.ducats = 15
		elif Flags.uncommon in self.flags: self.ducats = 45
		elif Flags.rare in self.flags: self.ducats = 100
		return self.ducats
	def createinfostring(self,displaymode):
		info = [i.name for i in Flags if i in self.flags and i in displaymode]
		if not info: return self.fullname
		elif info == ["vaulted"]: infostring = "V"
		else: infostring = tools.capitalizefirst("/".join(info))
		return self.fullname + " (" + infostring + ")"
	def __str__(self): return self.createinfostring(Component.defaultdisplaymode)
	__repr__ = __str__

@total_ordering
class Relic(metaclass=IndexClass):
	rarities = {
		"intact":		{Flags.common:0.25,Flags.uncommon:0.11,Flags.rare:0.02},
		"exceptional":	{Flags.common:0.23,Flags.uncommon:0.13,Flags.rare:0.04},
		"flawless":		{Flags.common:0.20,Flags.uncommon:0.17,Flags.rare:0.06},
		"radiant":		{Flags.common:0.17,Flags.uncommon:0.20,Flags.rare:0.10}
	}
	defaultdisplaymode = Flags.rare | Flags.wanted | Flags.vaulted
	def __init__(self,tier,name,stringcontents):
		self.tier = tier
		self.name = name
		self.stringcontents = stringcontents
		self.fullname = tier + " " + name
		self.flags = Flags(0)
		Relic[self.fullname] = self
	def createcontents(self):
		self.commoncontents = []
		self.uncommoncontents = []
		self.rarecontents = []
		for i in self.stringcontents:
			if i.startswith("!!"): self.rarecontents.append(Component.database[i[2:]])
			elif i.startswith("!"): self.uncommoncontents.append(Component.database[i[1:]])
			else: self.commoncontents.append(Component.database[i])
		self.contents = self.commoncontents + self.uncommoncontents + self.rarecontents
		for i in self.contents: i.relics.append(self)
		self.setrarities()
		return self.contents
	def setrarities(self):
		for i in self.commoncontents: i.flags |= Flags.common
		for i in self.uncommoncontents: i.flags |= Flags.uncommon
		for i in self.rarecontents: i.flags |= Flags.rare
		for i in self.contents: i.updateducats()
		return self
	def averageducats(self,refinement="intact"):
		ducats = 0
		for i in self.commoncontents: ducats += Relic.rarities[refinement][Flags.common]*i.ducats
		for i in self.uncommoncontents: ducats += Relic.rarities[refinement][Flags.uncommon]*i.ducats
		for i in self.rarecontents: ducats += Relic.rarities[refinement][Flags.rare]*i.ducats
		return ducats
	def createinfostring(self,displaymode,subdisplaymode=None):
		contentsinfo = []
		metainfo = []
		for i in Flags:
			if i in displaymode:
				if i == Flags.common: contentsinfo += self.commoncontents
				elif i == Flags.uncommon: contentsinfo += self.commoncontents
				elif i == Flags.rare: contentsinfo += self.rarecontents
				elif i in self.flags: metainfo.append(i.name)
		if contentsinfo: contentsstring = " [" + ", ".join(i.createinfostring(subdisplaymode) for i in contentsinfo) + "]"
		else: contentsstring = ""
		if metainfo: metastring = " (" + tools.capitalizefirst("/".join(metainfo)) + ")"
		else: metastring = ""
		return self.fullname + contentsstring + metastring
	def __str__(self): return self.createinfostring(Relic.defaultdisplaymode,Relic.defaultdisplaymode)
	__repr__ = __str__
	def __eq__(self,other): return self is other
	def __gt__(self,other):
		if self.tier == other.tier: return self.name > other.name
		elif self.tier == "Axi" or other.tier == "Lith": return True
		elif self.tier == "Lith" or other.tier == "Axi": return False
		elif self.tier == "Neo": return True
		elif self.tier == "Meso": return False

parseall()

def bestducats(allowvaulted=False):
	bestducats = 0
	bestrelic = None
	for i in Relic:
		if allowvaulted or not Flags.vaulted in i.flags:
			ducats = i.averageducats()
			if ducats > bestducats:
				bestducats = ducats
				bestrelic = i
	return (bestrelic,bestducats)

def containsmixedrarity(): return [i for i in Relic if any(j.ducats in (25,65) for j in i.contents)]

def farmablerelic(relic): return Flags.vaulted not in relic.flags and Flags.wanted not in relic.rarecontents[0].flags

def farmingrelics(): 
	farminglist = [i for i in Relic if farmablerelic(i)]
	prioritylist = [i for i in farminglist if Flags.wanted in i.flags]
	return (prioritylist,[i for i in farminglist if i not in prioritylist])

def categorize():
	useless = []
	common = []
	uncommon = []
	rare = []
	vaulted = []
	for r in Relic:
		if Flags.vaulted in r.flags: vaulted.append(r)
		elif Flags.wanted in r.rarecontents[0].flags: rare.append(r)
		elif any(Flags.wanted in i.flags for i in r.uncommoncontents): uncommon.append(r)
		elif any(Flags.wanted in i.flags for i in r.commoncontents): common.append(r)
		else: useless.append(r)
	return {"useless":useless,"common":common,"uncommon":uncommon,"rare":rare,"vaulted":vaulted}

def displayfarmingrelics():
	prioritylist,farminglist = farmingrelics()
	if len(prioritylist) >= 12: print("Priorities:\n\t" + tabbedtierordering(prioritylist))
	elif prioritylist: print("Priorities: " + lineartierordering(prioritylist))
	if len(farminglist) >= 12: print("Other farming relics:\n\t" + tabbedtierordering(farminglist))
	elif farminglist: print("Other farming relics: " + lineartierordering(farminglist))

def displaycategories():
	categories = categorize()
	for c in categories:
		if len(categories[c]) >= 12: print(tools.capitalizefirst(c) + ":\n\t" + tabbedtierordering(categories[c]))
		elif categories[c]: print(tools.capitalizefirst(c) + ": " + lineartierordering(categories[c]))

def separatetiers(relics):
	tiers = {"Lith":[],"Meso":[],"Neo":[],"Axi":[]}
	for i in relics: tiers[i.tier].append(i)
	for i in tiers.values(): i.sort()
	tierstrings = []
	for i in tiers:
		if tiers[i]: tierstrings.append(i+ " " + ", ".join(j.name for j in tiers[i]))
	return tierstrings

def tabbedtierordering(relics): return "\n\t".join(separatetiers(relics))

def lineartierordering(relics): return ", ".join(separatetiers(relics))

def displaywishlist():
	items = {}
	for i in Component:
		if Flags.wanted in i.flags:
			if i.item in items: items[i.item].append(i)
			else: items[i.item] = [i]
	itemstrings = []
	for i in items.values():
		componentstrings = []
		for c in i:
			if not c.relics: componentstrings.append(c.fullname + ": Unknown, vaulted")
			else:
				vaultedstrings = []
				unvaultedstrings = []
				for r in c.relics:
					if Flags.vaulted in r.flags: vaultedstrings.append(componentinrelicstring(c,r))
					else: unvaultedstrings.append(componentinrelicstring(c,r))
				componentstrings.append(c.fullname + ": " + ", ".join(vaultedstrings+unvaultedstrings))
		itemstrings.append("\n".join(componentstrings))
	print("\n\n".join(itemstrings))

def componentinrelicstring(component,relic):
	string = relic.fullname
	if component in relic.commoncontents: string += " C"
	elif component in relic.uncommoncontents: string += " U"
	elif component in relic.rarecontents: string += " R"
	if Flags.vaulted in relic.flags: string += " (V)"
	return string