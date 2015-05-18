#!/usr/bin/python
import sys
import os
from collections import defaultdict

mappings = {
	'HIGH'       : 'arduinoConstant',
	'abs'        : 'arduinoStdFunc',
	'arduinoFunc': 'analogReference',
	'setup'      : 'arduinoMethod',
	'begin'      : 'arduinoMethod',
	'bitSet'     : 'arduinoFunc',
	'analogRead' : 'arduinoFunc',
	'Serial'     : 'arduinoModule',
	'boolean'    : 'arduinoType',
	'+='         : None,
}

cppkeywords = set([
	'auto', 'const', 'double', 'float', 'int', 'short', 'struct', 'unsigned',
	'break', 'continue', 'else', 'for', 'long', 'signed', 'switch', 'void',
	'case', 'default', 'enum', 'goto', 'register', 'sizeof', 'typedef', 'volatile',
	'char', 'do', 'extern', 'if', 'return', 'static', 'union', 'while',
	'asm', 'dynamic_cast', 'namespace', 'reinterpret_cast', 'try',
	'bool', 'explicit', 'new', 'static_cast', 'typeid',
	'catch', 'false', 'operator', 'template', 'typename',
	'class', 'friend', 'private', 'this', 'using',
	'const_cast', 'inline', 'public', 'throw', 'virtual',
	'delete', 'mutable', 'protected', 'true', 'wchar_t',
])

def get_keywords(fileobj):
	heading = ''
	paragraph = 0

	for rawline in fileobj:
		line = rawline.rstrip('\r\n')
		if line.strip() == '':
			paragraph += 1
			continue
		elif line[0] == '#':
			heading = line[1:].strip()
		else:
			keyword, classname = line.split('\t')[:2]
			yield keyword, classname, heading, paragraph

def get_sections(fileobj):
	sections = defaultdict(lambda: [])

	for keyword, classname, heading, paragraph in get_keywords(fileobj):
		section_id = '%d-%s' % (paragraph, classname)
		sections[section_id].append(keyword)
	return sections

def get_mapped_keywords(sections):
	for keywords in sections.values():
		maps_to = [mappings[keyword] for keyword in keywords if (keyword in mappings)]
		reduced = filter(lambda x: x not in cppkeywords, keywords)

		if len(maps_to) == 1:
			if maps_to[0]:
				yield (reduced, maps_to[0])
		elif len(maps_to) == 0:
			print >> sys.stderr, ('Warning: No mapping for %s' % str(keywords))
		else:
			print >> sys.stderr, ('Warning: Collision for %s. Maps to: %s' % (str(keywords), ', '.join(maps_to)))

def get_syntax_groups(sections):
	syntax_groups = defaultdict(lambda: [])

	for keywords, mapping in get_mapped_keywords(sections):
		syntax_groups[mapping].extend(keywords)
	
	return syntax_groups


def get_syntax_definitions(filename):
	sections      = get_sections(open(filename))
	syntax_groups = sorted(get_syntax_groups(sections).items())
	caseinsensitive_cmp = lambda x,y: cmp(x.lower(), y.lower())

	for name, keywords in syntax_groups:
		linestart = 'syn keyword %-16s' % name
		line      = linestart
		lines     = ''

		for keyword in sorted(set(keywords), caseinsensitive_cmp):
			if len(line) + len(keyword) > 80:
				lines += line
				line   = '\n' + linestart

			line += ' ' + keyword

		lines += line

		yield lines

def get_arduino_version(shared_dir):
	try:
		revision_file = os.path.join(shared_dir, 'revisions.txt')
		revision = open(revision_file).next().rstrip('\r\n') # first line
	except:
		revision = 'unknown'
	return revision


def main(argv):
	import datetime
	import string
	arduino_dir  = '.' if len(argv) == 1 else argv[1]
	shared_dir   = os.path.join(arduino_dir, 'build', 'shared')
	keyword_file = os.path.join(shared_dir,  'lib', 'keywords.txt')

	template = string.Template(open('template.vim').read())

	sys.stdout.write(template.substitute({
		'rules': '\n\n'.join(get_syntax_definitions(keyword_file)),
		'date':  datetime.datetime.now().strftime('%d %B %Y'),
		'arduino_version': get_arduino_version(shared_dir),
	}))

if __name__=='__main__':
	import sys
	main(sys.argv)
