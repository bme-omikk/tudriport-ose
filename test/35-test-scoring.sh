DIRNAME=$(readlink -f $(dirname $0))
TESTBASEDIR=$DIRNAME
BASEDIR=$DIRNAME/..

. $DIRNAME/lib/initialize-database.sh

set -e

echo "===== Initializing database "
initializeDatabase 
#riportkeszites-django/riport/manage.py file2db --trydebug -M2 test/resources/mtmt2-json/test1_publications.json.gz
#riportkeszites-django/riport/manage.py file2db --trydebug -M2 test/resources/mtmt2-json/test2_publications.json.gz
#riportkeszites-django/riport/manage.py ext_authorlist --file test/resources/authors/example_faculty1_department1.txt --org EXAMPLE --unit FACULTY1 --subunit DEPT1

echo "===== Testing"
riportkeszites-django/riport/manage.py test riport.tests

