#! /usr/bin/python
import cgi
import cgitb

from core import *
from htmlCore import *
from playerstats import Totals, Skill
from copy import deepcopy

import urllib


cgitb.enable()


def main():
    form = cgi.FieldStorage()

    printJSONHeader()
    # Parse the data and show the page
    ladderData = parseLadderFiles()

    # setup all the objects which can give us statistics for a player
    playerstats = Totals(ladderData.games), Skill(ladderData.games)

    players = ladderData.getAllUnexcludedPlayers()
    players.sort(lambda x, y: cmp(y.getLastGame().getVar(y.name, "newSkill"), x.getLastGame().getVar(x.name, "newSkill")))

    if "mode" in form:
        if form['mode'].value == "ladder":
            print "["
            for i in range(len(players)):
                player = players[i]
                print "{ \"name\":\"" + player.name + "\","

                totals = playerstats[0]

                print "\"total\":{ \"for\":" + str(totals.totalFor[player.name]) + ", \"against\":" + str(totals.totalAgainst[player.name]) + ", \"games\":" + str(totals.gameCount[player.name]) + " },"
                print "\"gamesToday\":" + str(totals.todayGameCount[player.name]) + ","

                skill = playerstats[1]

                print "\"skill\":" + str(skill.skill[player.name].lastSkill()) + ","
                print "\"weaselFactor\":" + str(skill.weasel[player.name])  # + ","
                # TODO overrated (but there's lots of logic for this inside Skill)

                print "}"
                if i < len(players) - 1:
                    print ","
            print "]"

        elif form['mode'].value == "records":
            # highest and lowest ever skill.
            highestSkill = 0.0
            lowestSkill = 0.0

            print "{"

            for game in ladderData.games:
                blueSkill = game.getVar(game.blue, "newSkill")
                if blueSkill >= highestSkill:
                    highestSkill = blueSkill
                    highestSkillPlayer = game.blue
                    highestSkillTime = game.time
                if blueSkill <= lowestSkill:
                    lowestSkill = blueSkill
                    lowestSkillPlayer = game.blue
                    lowestSkillTime = game.time

                redSkill = game.getVar(game.red, "newSkill")
                if redSkill >= highestSkill:
                    highestSkill = redSkill
                    highestSkillPlayer = game.red
                    highestSkillTime = game.time
                if redSkill <= lowestSkill:
                    lowestSkill = redSkill
                    lowestSkillPlayer = game.red
                    lowestSkillTime = game.time
            print "\"highestSkill\":{\"name\":\"%(name)s\", \"skill\":%(skill)s, \"date\":%(date)s}," % {"name": highestSkillPlayer, "skill": highestSkill, "date": highestSkillTime}
            print "\"lowestSkill\":{\"name\":\"%(name)s\", \"skill\":%(skill)s, \"date\":%(date)s}" % {"name": lowestSkillPlayer, "skill": lowestSkill, "date": lowestSkillTime}
            print "\"mostSignificantGame\":"
              # most significant ever.
            mostSignificantChange = 0.0
            for game in ladderData.games:
                changeToBlue = game.getVar(game.blue, "skillChangeTo")
                if changeToBlue > mostSignificantChange:
                    mostSignificantChange = changeToBlue
                    mostSignificantGame = game

                changeToRed = game.getVar(game.red, "skillChangeTo")
                if changeToRed > mostSignificantChange:
                    mostSignificantChange = changeToRed
                    mostSignificantGame = game
            gameToJson(mostSignificantGame)
            print "}"

        elif form['mode'].value == "recent":
            # 10 most recent games
            print "["
            gamesToList = ladderData.games[-10:]
            gamesToList.reverse()
            for i in range(len(gamesToList)):
                gameToJson(gamesToList[i])
                if i < len(gamesToList) - 1:
                    print ","
            print "]"

        elif form['mode'].value == "recentSignificant":
            # recent significant games
            sigGames = [game for game in ladderData.games if game.isSignificant()]
            print "["
            gamesToList = sigGames[-10:]
            gamesToList.reverse()
            for i in range(len(gamesToList)):
                gameToJson(gamesToList[i])
                if i < len(gamesToList) - 1:
                    print ","
            print "]"

        elif form['mode'].value == "playerHistory":
            form = cgi.FieldStorage()
            if "name" in form:
                usernames = form.getlist('name')
            else:
                usernames = []

            plotData = DefaultDict([])
            Skill(ladderData.games)

            for game in ladderData.games:
                plotData[game.red].append((game.time, game.getVar(game.red, "oldSkill") + game.getVar(game.red, "skillChangeTo")))
                plotData[game.blue].append((game.time, game.getVar(game.blue, "oldSkill") + game.getVar(game.blue, "skillChangeTo")))

            for u in range(len(usernames)):
                user = usernames[u]
                print """"%(name)s":[""" % {"name": user}
                userSkill = plotData[user]
                for i in range(len(userSkill)):
                    print """{"date":%(date)s, "skill":%(skill)s}%(maybeComma)s""" % {"date": userSkill[i][0], "skill": userSkill[i][1], "maybeComma": "," if i < (len(userSkill) - 1) else ""}
                if i < len(userSkill) - 1:
                    print "],"
                else:
                    print "]"


def gameToJson(game):
    print """
{
  "red" : {
    "name" : "%(redName)s",
    "score" : %(redScore)s,
    "skillChange" : %(redSkillChange)s
  },
  "blue" : {
    "name" : "%(blueName)s",
    "score" : %(blueScore)s,
    "skillChange" : %(blueSkillChange)s
  },
  "date" : %(date)s
}""" % {"redName": game.red, "redScore": game.redScore, "redSkillChange": game.getVar(game.red, "skillChangeTo"), "blueName": game.blue, "blueScore": game.blueScore, "blueSkillChange": game.getVar(game.blue, "skillChangeTo"), "date": game.time}


class DefaultDict(dict):
    """Dictionary with a default value for unknown keys."""
    def __init__(self, default):
        self.default = default

    def __getitem__(self, key):
        if key in self:
            return self.get(key)
        return self.setdefault(key, deepcopy(self.default))

    def __copy__(self):
        copy = DefaultDict(self.default)
        copy.update(self)
        return copy

main()
