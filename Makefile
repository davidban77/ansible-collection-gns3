VERSION=1.3.0

build:
	rm -rf releases/
	mazer build

publish: build
	mazer publish releases/davidban77-gns3-${VERSION}.tar.gz

test-create-lab:
	cd test/playbooks; ansible-playbook main.yml -e execute=create

test-create-files:
	cd test/playbooks; ansible-playbook create_files.yml

test-delete-files:
	cd test/playbooks; ansible-playbook delete_files.yml

test-delete-lab:
	cd test/playbooks; ansible-playbook main.yml -e execute=delete

test-create-env: test-create-lab test-create-files

test-delete-env: test-delete-files test-delete-lab
