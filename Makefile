VERSION=1.5.0

build:
	rm -rf releases/
	mazer build

publish: build
	mazer publish releases/davidban77-gns3-${VERSION}.tar.gz

test-create-lab:
	cd test/playbooks; ansible-playbook main.yml -e execute=create

test-node-interaction:
	cd test/playbooks; ansible-playbook node_interaction.yml

test-create-files:
	cd test/playbooks; ansible-playbook create_files.yml

test-snapshots:
	cd test/playbooks; ansible-playbook snapshots.yml

test-delete-files:
	cd test/playbooks; ansible-playbook delete_files.yml

test-delete-lab:
	cd test/playbooks; ansible-playbook main.yml -e execute=delete

test-create-all: test-create-lab test-create-files test-node-interaction test-snapshots

test-delete-all: test-delete-files test-delete-lab
