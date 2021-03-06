#!/bin/bash
#
# Script to make a ${project_name} macOS distribution package.
#
# This file is generated by l2tdevtools update-dependencies.py, any dependency
# related changes should be made in dependencies.ini.

EXIT_SUCCESS=0;
EXIT_FAILURE=1;

DEPENDENCIES="${dependencies}";

MACOS_VERSION=`sw_vers -productVersion | awk -F '.' '{print $$1 "." $$2}'`;

PROJECT_VERSION=`grep -e '^__version' ${project_name}/__init__.py | sed -e "s/^[^=]*= '\([^']*\)'/\1/g"`;
DEPENDENCIES_PATH="../l2tdevtools/build";
LICENSES_PATH="../l2tdevtools/data/licenses";

PKG_FILENAME="../python-${project_name}-$${PROJECT_VERSION}.pkg";
DISTDIR="${project_name}-$${PROJECT_VERSION}";

if test ! -d $${DEPENDENCIES_PATH};
then
  echo "Missing dependencies directory: $${DEPENDENCIES_PATH}.";

  exit $${EXIT_FAILURE};
fi

if test ! -d config;
then
  echo "Missing config directory.";

  exit $${EXIT_FAILURE};
fi

if test -z "$$1";
then
  DIST_VERSION="$${PROJECT_VERSION}";
else
  DIST_VERSION="$${PROJECT_VERSION}-$$1";
fi

DISTFILE="../${project_name}-$${DIST_VERSION}-macos-$${MACOS_VERSION}.dmg";

rm -rf build dist tmp $${DISTDIR} $${PKG_FILENAME} $${DISTFILE};

python setup.py install --root=$$PWD/tmp --install-data=/usr/local

mkdir -p tmp/usr/local/share/doc/${project_name}
cp AUTHORS ACKNOWLEDGEMENTS LICENSE tmp/usr/local/share/doc/${project_name}

for PY_FILE in tmp/usr/local/bin/*.py;
do
  # Rewrite the shebang of the Python script since MacOS uses Python 2.7
  sed -i $${PY_FILE} 's?#!/usr/bin/env python3?#!/usr/bin/env python?';

  SH_FILE=$${PY_FILE/.py/.sh};
  cat > $${SH_FILE} << EOT
#!/bin/sh
PYTHONPATH=/Library/Python/2.7/site-packages/ \$${0/.sh/.py} \$$*;
EOT
  chmod a+x $${SH_FILE};
done

pkgbuild --root tmp --identifier "com.github.log2timeline.${project_name}" --version $${PROJECT_VERSION} --ownership recommended $${PKG_FILENAME};

if test ! -f $${PKG_FILENAME};
then
  echo "Missing ${project_name} package file: $${PKG_FILENAME}";

  exit $${EXIT_FAILURE};
fi

mkdir $${DISTDIR};

cp config/macos/Readme.txt $${DISTDIR}/;
sed "s/@VERSION@/$${PROJECT_VERSION}/" config/macos/install.sh > $${DISTDIR}/install.sh;
cp config/macos/uninstall.sh $${DISTDIR}/;

chmod 755 $${DISTDIR}/install.sh $${DISTDIR}/uninstall.sh;

mkdir $${DISTDIR}/licenses;
mkdir $${DISTDIR}/packages;

for DEPENDENCY in $${DEPENDENCIES};
do
  DEPENDENCY_DMG=`ls -1 $${DEPENDENCIES_PATH}/$${DEPENDENCY}-*.dmg`;

  if test -z $${DEPENDENCY_DMG};
  then
    continue;
  fi
  DEPENDENCY_PKG=`basename $${DEPENDENCY_DMG/.dmg/.pkg}`;

  hdiutil attach $${DEPENDENCY_DMG};
  cp -rf /Volumes/$${DEPENDENCY_PKG}/$${DEPENDENCY_PKG} $${DISTDIR}/packages;
  hdiutil detach /Volumes/$${DEPENDENCY_PKG};

  LICENSE_FILE="$${LICENSES_PATH}/LICENSE.$${DEPENDENCY}";

  if test -f $${LICENSE_FILE};
  then
    cp $${LICENSE_FILE} $${DISTDIR}/licenses;
  fi
done

cp -rf $${PKG_FILENAME} $${DISTDIR}/packages;

hdiutil create $${DISTFILE} -srcfolder $${DISTDIR}/ -fs HFS+;

exit $${EXIT_SUCCESS};

