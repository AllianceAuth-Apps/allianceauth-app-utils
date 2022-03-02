appname = allianceauth-app-utils
package = app_utils

help:
	@echo "Makefile for $(appname)"

coverage:
	coverage run ../myauth/manage.py test utils_test_app.tests --keepdb --failfast && coverage html && coverage report -m

test:
	# runs a full test incl. re-creating of the test DB
	python ../myauth/manage.py test $(package) --failfast --debug-mode -v 2

pylint:
	pylint $(package)

check_complexity:
	flake8 $(package) --max-complexity=10

nuke_testdb:
	# This will delete the current test database
	# very userful after large changes to the models
	sudo mysql -u root -e "drop database test_aa_dev_4;"

flake8:
	flake8 $(package) --count

create_testdata:
	python ../myauth/manage.py test $(package).tests.testdata.create_eveuniverse --keepdb -v 2
