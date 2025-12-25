#!/bin/bash
set -e

PKG_NAME="auto-idle"
NEW_VERSION="0.1.3"
OLD_VERSION="0.1.2"

OLD_DEB="deb/${PKG_NAME}_${OLD_VERSION}"
NEW_DEB="deb/${PKG_NAME}_${NEW_VERSION}"

echo "Building ${PKG_NAME} ${NEW_VERSION}"

# ---- sanity checks -------------------------------------------------

if [ ! -d "$OLD_DEB" ]; then
  echo "ERROR: old package tree $OLD_DEB not found"
  exit 1
fi

if [ ! -f "$OLD_DEB/DEBIAN/control" ]; then
  echo "ERROR: missing control file in $OLD_DEB"
  exit 1
fi

# ---- update project metadata --------------------------------------

sed -i "s/^version = \".*\"/version = \"$NEW_VERSION\"/" pyproject.toml

# ---- create clean staging directory --------------------------------

rm -rf "$NEW_DEB"
mkdir -p \
  "$NEW_DEB/DEBIAN" \
  "$NEW_DEB/usr/bin" \
  "$NEW_DEB/usr/share"

# ---- copy ONLY required files -------------------------------------

# control & lifecycle scripts
cp "$OLD_DEB/DEBIAN/control"  "$NEW_DEB/DEBIAN/control"
cp "$OLD_DEB/DEBIAN/postinst" "$NEW_DEB/DEBIAN/postinst"
cp "$OLD_DEB/DEBIAN/prerm"    "$NEW_DEB/DEBIAN/prerm"

# runtime files
cp "$OLD_DEB/usr/bin/auto-idle" "$NEW_DEB/usr/bin/auto-idle"
cp -r "$OLD_DEB/usr/share/auto-idle" "$NEW_DEB/usr/share/"
cp -r "$OLD_DEB/usr/share/applications" "$NEW_DEB/usr/share/"
cp -r "$OLD_DEB/usr/share/icons" "$NEW_DEB/usr/share/"
#cp app-auto-idle-power.py "$BUILD_DIR/usr/share/auto-idle/"

cp -r app-auto-idle-power.py "$NEW_DEB/usr/share/auto-idle/"
cp -r config "$NEW_DEB/usr/share/auto-idle/"
cp -r gui "$NEW_DEB/usr/share/auto-idle/"

# ---- update control version ---------------------------------------

sed -i "s/^Version: .*/Version: ${NEW_VERSION}/" \
  "$NEW_DEB/DEBIAN/control"

# ---- fix launcher --------------------------------------------------

sed -i 's|^exec python3|exec /usr/bin/python3|' \
  "$NEW_DEB/usr/bin/auto-idle"

# ---- permissions (important) --------------------------------------

chmod 755 "$NEW_DEB/usr/bin/auto-idle"
chmod 755 "$NEW_DEB/DEBIAN/postinst"
chmod 755 "$NEW_DEB/DEBIAN/prerm"
chmod 644 "$NEW_DEB/DEBIAN/control"

# ---- ownership (dpkg requirement) ---------------------------------

sudo chown -R root:root "$NEW_DEB"

# ---- build ---------------------------------------------------------

dpkg-deb --build "$NEW_DEB"

# ---- restore ownership for git sanity -----------------------------

sudo chown -R "$USER:$USER" deb

echo "✔ Package built: deb/${PKG_NAME}_${NEW_VERSION}.deb"
