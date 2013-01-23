# Released under a BSD license. Copyright Bryan Helmig 2010.

# modified from http://bryanhelmig.com/python-crossword-puzzle-generator/

import random, re, time, string
from copy import copy as duplicate
import json 

# optional, speeds up by a factor of 4
# import psyco
# psyco.full()
 
class Crossword(object):
    def __init__(self, cols, rows, empty = '-', maxloops = 2000, available_words=[]):
        self.cols = cols
        self.rows = rows
        self.empty = empty
        self.maxloops = maxloops
        self.available_words = available_words
        self.randomize_word_list()
        self.current_word_list = []
        self.debug = 0
        self.clear_grid()
 
    def clear_grid(self): # initialize grid and fill with empty character
        self.grid = []
        for i in range(self.rows):
            ea_row = []
            for j in range(self.cols):
                ea_row.append(self.empty)
            self.grid.append(ea_row)
 
    def randomize_word_list(self): # also resets words and sorts by length
        temp_list = []
        for word in self.available_words:
            if isinstance(word, Word):
                temp_list.append(Word(word.word, word.clue))
            else:
                temp_list.append(Word(word[0], word[1]))
        random.shuffle(temp_list) # randomize word list
        temp_list.sort(key=lambda i: len(i.word), reverse=True) # sort by length
        self.available_words = temp_list
 
    def compute_crossword(self, time_permitted = 1.00, spins=2):
        time_permitted = float(time_permitted)
 
        count = 0
        copy = Crossword(self.cols, self.rows, self.empty, self.maxloops, self.available_words)
 
        start_full = float(time.time())
        while (float(time.time()) - start_full) < time_permitted or count == 0: # only run for x seconds
            self.debug += 1
            copy.current_word_list = []
            copy.clear_grid()
            copy.randomize_word_list()
            x = 0
            while x < spins: # spins; 2 seems to be plenty
                for word in copy.available_words:
                    if word not in copy.current_word_list:
                        copy.fit_and_add(word)
                x += 1
            #print copy.solution()
            #print len(copy.current_word_list), len(self.current_word_list), self.debug
            # buffer the best crossword by comparing placed words
            if len(copy.current_word_list) > len(self.current_word_list):
                self.current_word_list = copy.current_word_list
                self.grid = copy.grid
            count += 1
        return
 
    def suggest_coord(self, word):
        count = 0
        coordlist = []
        glc = -1
        for given_letter in word.word: # cycle through letters in word
            glc += 1
            rowc = 0
            for row in self.grid: # cycle through rows
                rowc += 1
                colc = 0
                for cell in row: # cycle through  letters in rows
                    colc += 1
                    if given_letter == cell: # check match letter in word to letters in row
                        try: # suggest vertical placement 
                            if rowc - glc > 0: # make sure we're not suggesting a starting point off the grid
                                if ((rowc - glc) + word.length) <= self.rows: # make sure word doesn't go off of grid
                                    coordlist.append([colc, rowc - glc, 1, colc + (rowc - glc), 0])
                        except: pass
                        try: # suggest horizontal placement 
                            if colc - glc > 0: # make sure we're not suggesting a starting point off the grid
                                if ((colc - glc) + word.length) <= self.cols: # make sure word doesn't go off of grid
                                    coordlist.append([colc - glc, rowc, 0, rowc + (colc - glc), 0])
                        except: pass
        # example: coordlist[0] = [col, row, vertical, col + row, score]
        #print word.word
        #print coordlist
        new_coordlist = self.sort_coordlist(coordlist, word)
        #print new_coordlist
        return new_coordlist
 
    def sort_coordlist(self, coordlist, word): # give each coordinate a score, then sort
        new_coordlist = []
        for coord in coordlist:
            col, row, vertical = coord[0], coord[1], coord[2]
            coord[4] = self.check_fit_score(col, row, vertical, word) # checking scores
            if coord[4]: # 0 scores are filtered
                new_coordlist.append(coord)
        random.shuffle(new_coordlist) # randomize coord list; why not?
        new_coordlist.sort(key=lambda i: i[4], reverse=True) # put the best scores first
        return new_coordlist
 
    def fit_and_add(self, word): # doesn't really check fit except for the first word; otherwise just adds if score is good
        fit = False
        count = 0
        coordlist = self.suggest_coord(word)
 
        while not fit and count < self.maxloops:
 
            if len(self.current_word_list) == 0: # this is the first word: the seed
                # top left seed of longest word yields best results (maybe override)
                vertical, col, row = random.randrange(0, 2), 1, 1
                ''' 
                # optional center seed method, slower and less keyword placement
                if vertical:
                    col = int(round((self.cols + 1)/2, 0))
                    row = int(round((self.rows + 1)/2, 0)) - int(round((word.length + 1)/2, 0))
                else:
                    col = int(round((self.cols + 1)/2, 0)) - int(round((word.length + 1)/2, 0))
                    row = int(round((self.rows + 1)/2, 0))
                # completely random seed method
                col = random.randrange(1, self.cols + 1)
                row = random.randrange(1, self.rows + 1)
                '''
 
                if self.check_fit_score(col, row, vertical, word): 
                    fit = True
                    self.set_word(col, row, vertical, word, force=True)
            else: # a subsquent words have scores calculated
                try: 
                    col, row, vertical = coordlist[count][0], coordlist[count][1], coordlist[count][2]
                except IndexError: return # no more cordinates, stop trying to fit
 
                if coordlist[count][4]: # already filtered these out, but double check
                    fit = True 
                    self.set_word(col, row, vertical, word, force=True)
 
            count += 1
        return
 
    def check_fit_score(self, col, row, vertical, word):
        '''
        And return score (0 signifies no fit). 1 means a fit, 2+ means a cross.
 
        The more crosses the better.
        '''
        if col < 1 or row < 1:
            return 0
 
        count, score = 1, 1 # give score a standard value of 1, will override with 0 if collisions detected
        for letter in word.word:            
            try:
                active_cell = self.get_cell(col, row)
            except IndexError:
                return 0
 
            if active_cell == self.empty or active_cell == letter:
                pass
            else:
                return 0
 
            if active_cell == letter:
                score += 1
 
            if vertical:
                # check surroundings
                if active_cell != letter: # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col+1, row): # check right cell
                        return 0
 
                    if not self.check_if_cell_clear(col-1, row): # check left cell
                        return 0
 
                if count == 1: # check top cell only on first letter
                    if not self.check_if_cell_clear(col, row-1):
                        return 0
 
                if count == len(word.word): # check bottom cell only on last letter
                    if not self.check_if_cell_clear(col, row+1): 
                        return 0
            else: # else horizontal
                # check surroundings
                if active_cell != letter: # don't check surroundings if cross point
                    if not self.check_if_cell_clear(col, row-1): # check top cell
                        return 0
 
                    if not self.check_if_cell_clear(col, row+1): # check bottom cell
                        return 0
 
                if count == 1: # check left cell only on first letter
                    if not self.check_if_cell_clear(col-1, row):
                        return 0
 
                if count == len(word.word): # check right cell only on last letter
                    if not self.check_if_cell_clear(col+1, row):
                        return 0
 
 
            if vertical: # progress to next letter and position
                row += 1
            else: # else horizontal
                col += 1
 
            count += 1
 
        return score
 
    def set_word(self, col, row, vertical, word, force=False): # also adds word to word list
        if force:
            word.col = col
            word.row = row
            word.vertical = vertical
            self.current_word_list.append(word)
 
            for letter in word.word:
                self.set_cell(col, row, letter)
                if vertical:
                    row += 1
                else:
                    col += 1
        return
 
    def set_cell(self, col, row, value):
        self.grid[row-1][col-1] = value
 
    def get_cell(self, col, row):
        return self.grid[row-1][col-1]
 
    def check_if_cell_clear(self, col, row):
        try:
            cell = self.get_cell(col, row)
            if cell == self.empty: 
                return True
        except IndexError:
            pass
        return False
 
    def solution(self): # return solution grid
        outStr = ""
        for r in range(self.rows):
            for c in self.grid[r]:
                outStr += '%s ' % c
            outStr += '\n'
        return outStr
 
    def word_find(self): # return solution grid
        outStr = ""
        for r in range(self.rows):
            for c in self.grid[r]:
                if c == self.empty:
                    outStr += '%s ' % string.lowercase[random.randint(0,len(string.lowercase)-1)]
                else:
                    outStr += '%s ' % c
            outStr += '\n'
        return outStr
 
    def order_number_words(self): # orders words and applies numbering system to them
        self.current_word_list.sort(key=lambda i: (i.col + i.row))
        count, icount = 1, 1
        for word in self.current_word_list:
            word.number = count
            if icount < len(self.current_word_list):
                if word.col == self.current_word_list[icount].col and word.row == self.current_word_list[icount].row:
                    pass
                else:
                    count += 1
            icount += 1
 
    def display(self, order=True): # return (and order/number wordlist) the grid minus the words adding the numbers
        outStr = ""
        if order:
            self.order_number_words()
 
        copy = self
 
        for word in self.current_word_list:
            copy.set_cell(word.col, word.row, word.number)
 
        for r in range(copy.rows):
            for c in copy.grid[r]:
                outStr += '%s ' % c
            outStr += '\n'
 
        outStr = re.sub(r'[a-z]', ' ', outStr)
        return outStr
 
    def word_bank(self): 
        outStr = ''
        temp_list = duplicate(self.current_word_list)
        random.shuffle(temp_list) # randomize word list
        for word in temp_list:
            outStr += '%s\n' % word.word
        return outStr
 
    def legend(self): # must order first
        outStr = ''
        for word in self.current_word_list:
            outStr += '%d. (%d,%d) %s: %s\n' % (word.number, word.col, word.row, word.down_across(), word.clue )
        return outStr

    def jsondict(self):
        words = []
        self.order_number_words()
        for idx, w in enumerate(self.current_word_list):
            d = w.jsondict()
#            d['position'] = idx 
            words.append(d)
        return words
 
class Word(object):
    def __init__(self, word=None, clue=None):
        self.word = re.sub(r'\s', '', word.lower())
        self.clue = clue
        self.length = len(self.word)
        # the below are set when placed on board
        self.row = None
        self.col = None
        self.vertical = None
        self.number = None
 
    def down_across(self): # return down or across
        if self.vertical: 
            return 'down'
        else: 
            return 'across'
 
    def __repr__(self):
        return '<Word: %s>' %  self.word

    def jsondict(self):
        return {
            'answer': self.word,
            'clue': '%s. %s' % (self.number, self.clue),
            'position': self.number - 1,
            'orientation': 'down' if self.vertical else 'across',
            'startx': self.col,
            'starty': self.row
        }
 
### end class, start execution
 
#start_full = float(time.time())

# Puzzle 1
word_list_1 = (
    ['masjidjamek', 'One of the oldest mosques in Kuala Lumpur (2 words)'],
    ['raja', 'St. Mary\'s Cathedral is located in which Jalan?'],
    ['satay', 'Famous food in Kajang'],
    ['bungapakme', 'The name of Rafflesia flower in Malay (2 words)'],
    ['penang','Biggest Murugan temple outside of India is located in this city'],
    ['nasikerabu','A Malay rice dish'],
    ['szeya', 'The oldest Taoist temple in Kuala Lumpur (2 words)'],
    ['wau','___ is an intricately designed Malaysian moon-kite'],
    ['kelantan','In which state we can find the largest Sitting Buddha in Asia?'],
    ['snake','The zodiac for 2013 in Chinese calendar'],
    ['tamil','This ethnic includes 75% of Malaysian Indians'],
)

# Puzzle 2
word_list_2 = (
    ['twelve', 'How many signs does the Chinese Zodiac have?'],
    ['soorapadam', (
        'Many of the shrines in Batu Cave relates to the story of '
        'Lord Murugan\'s victory over this demon')],
    ['shafi\'i', 'The official school of Sunni Islam in Malaysia'],
    ['linut', ('Sticky broiled sago flour, normally complemented with with '
        'shrimp paste which is popular in Sarawak')],
    ['khadijah', 'Name of the most famous wet market in Malaysia'],
    ['indonesia', 'the largest Muslim majority country in the world'],
    ['ujongtanah', 'what is the previous name of Johor in Malay (2 words)'],
    ['shiva', 'This deity is worshipped by large number of Hindu in Malaysia'],
)

# Puzzle 3
word_list_3 = (
    ['cow', 'Sacred animal in Hinduism'],
    ['rathayatra', (
        'A Hindu festival which held usually end of the year, '
        'when the deities placed on a chariot which is pulled '
        'through the streets by devotees')],
    ['baha\'i', ('This religion was introduced to people of Malaya '
        'by a Persian couple in 1950 and includes Chinese, Eurasian, '
        'Indian and Indigenous communities')],
    ['taoteching', 'The keystone work of literature in Taoism (3 words)'],
    ['datukkeramat', ('This religious belief in Malaysia is a fusion of '
        'pre-Islamic spirit belief, Sufi saint worship and Chinese folk '
        'religion (2 words)')],
    ['islam', 'One of the fastest growing religions in the world'],
    ['wuwei', 'Action through non-action in Taoism (2 words)'],
    ['silat', 'Malay local martial art']
)

word_list_4 = (
    ['thaipusam', ('A Hindu festival celebrated mostly by the Tamil '
        'community on January/February')],
    ['hajj', 'The largest relgularly occuring pilgrimage in the world'],
    ['deepavali', '"Row of lamps"'],
    ['rajang', 'The longest river in Malaysia'],
    ['cantonese', 'One of the Chinese dialects in Malaysia'],
    ['pahang', 'The third largest state in Malaysia'],
    ['namaskaram', '"Hello" (greeting) in Tamil'],
    ['gawaidayak', 'Harvest celebration in East Malaysia'],
    ['rendang', ('A spicy meat dish originated from the Minangkabau '
        'ethnic group')],
    ['salvation', ('Saving of the soul from the sin and its '
        'consequences in Christianity')],
    ['senoi', 'One of the three main category of Orang Asli people'],
)

def generate_crossword(wordlist):
    size = 0
    for entry in wordlist:
        word = entry[0]
        if len(word) > size:
            size = len(word)
    size = size + 2
    crossword = Crossword(size, size, ' ', 5000, wordlist)
    crossword.compute_crossword(5)
    return json.dumps(crossword.jsondict(), indent=2)

open('wsgi/static/puzzle1.json', 'w').write(generate_crossword(word_list_1))
open('wsgi/static/puzzle2.json', 'w').write(generate_crossword(word_list_2))
open('wsgi/static/puzzle3.json', 'w').write(generate_crossword(word_list_3))
open('wsgi/static/puzzle4.json', 'w').write(generate_crossword(word_list_4))
