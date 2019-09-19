VERSION=1.2.2

build:
	rm -rf releases/
	mazer build

publish: build
	mazer publish releases/davidban77-gns3-${VERSION}.tar.gz
