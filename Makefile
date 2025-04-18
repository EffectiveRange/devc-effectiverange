
TARGET_NAME=ARMHF-BULLSEYE
BASE_IMAGE_VER=latest
DEVC_ARCH=$(shell grep TARGET_ARCH= TARGET/$(TARGET_NAME)/target | cut -d'=' -f2)
KEEP_BUILD_ARTIFACTS=FALSE
BASE_DISTRO=$(shell grep VERSION_CODENAME= TARGET/$(TARGET_NAME)/target | cut -d'=' -f2)
CROSS_BASE_IMAGE_VER=$(BASE_DISTRO)-slim
colon := :
$(colon) := :
IMG_TAG=$(TARGET_NAME)-$$(date +%Y%m%d-%H%M%S)

.PHONY: base-armhf base-amd64 devc devc-armhf devc-amd64 build_driver cross-armhf devc-arm64

build_driver:
	if [ $$(id -u) -eq "0" ] ; then apt update && apt install -y  qemu-user-static qemu-utils binfmt-support;\
	elif sudo -n true 2> /dev/null;then sudo apt update && sudo apt install -y  qemu-user-static qemu-utils binfmt-support;\
	fi

cross-armhf: build_driver
	CROSS_IMG_VER=$$(./scripts/gen_cross_hash $(DEVC_ARCH) TARGET/$(TARGET_NAME) 2>/dev/null ); echo Cross image version is $$CROSS_IMG_VER ;\
	if [ "$$(./scripts/check_cross_base $(DEVC_ARCH) TARGET/$(TARGET_NAME))" = "true" ]; then \
		docker buildx build --file Dockerfile-cross --tag effectiverange/$(DEVC_ARCH)-$(BASE_DISTRO)-tools-cross$(:)$$CROSS_IMG_VER --build-arg BASE_IMAGE_VER=$(CROSS_BASE_IMAGE_VER) --build-arg TARGET_DIR=TARGET/$(TARGET_NAME) --build-arg KEEP_BUILD_ARTIFACTS=$(KEEP_BUILD_ARTIFACTS) . ;\
	fi 

base-armhf: cross-armhf
	docker buildx build .  --file Dockerfile --tag effectiverange/armhf-$(BASE_DISTRO)-tools-base$(:)$(IMG_TAG) --build-arg BASE_IMAGE_REPO=effectiverange/armhf-$(BASE_DISTRO)-tools-cross --build-arg BASE_IMAGE_VER=$$(./scripts/gen_cross_hash armhf TARGET/$(TARGET_NAME))  --build-arg TARGET_DIR=TARGET/$(TARGET_NAME) --build-arg KEEP_BUILD_ARTIFACTS=$(KEEP_BUILD_ARTIFACTS)

base-amd64:
	docker buildx build . --file Dockerfile --tag effectiverange/amd64-$(BASE_DISTRO)-tools-base$(:)$(IMG_TAG) --build-arg BASE_IMAGE_VER=$(CROSS_BASE_IMAGE_VER) --build-arg TARGET_DIR=TARGET/$(TARGET_NAME) --build-arg KEEP_BUILD_ARTIFACTS=$(KEEP_BUILD_ARTIFACTS) --build-arg BUILD_ARCH=amd64

base-arm64: cross-armhf
	docker buildx build . --file Dockerfile --tag effectiverange/arm64-$(BASE_DISTRO)-tools-base$(:)$(IMG_TAG) --build-arg BASE_IMAGE_REPO=effectiverange/arm64-$(BASE_DISTRO)-tools-cross --build-arg BASE_IMAGE_VER=$$(./scripts/gen_cross_hash armhf TARGET/$(TARGET_NAME)) --build-arg TARGET_DIR=TARGET/$(TARGET_NAME) --build-arg KEEP_BUILD_ARTIFACTS=$(KEEP_BUILD_ARTIFACTS) --build-arg BUILD_ARCH=arm64


devc-armhf:
	docker buildx build --file Dockerfile-devc --tag effectiverange/er-devc-armhf-$(BASE_DISTRO)$(:)$(IMG_TAG) --build-arg BASE_IMAGE_REPO=effectiverange/armhf-$(BASE_DISTRO)-tools-base --build-arg BASE_IMAGE_VER=$(BASE_IMAGE_VER) --build-arg DEVC_ARCH=armhf .

devc-amd64:
	docker buildx build --file Dockerfile-devc --tag  effectiverange/er-devc-amd64-$(BASE_DISTRO)$(:)$(IMG_TAG) --build-arg BASE_IMAGE_REPO=effectiverange/amd64-$(BASE_DISTRO)-tools-base --build-arg BASE_IMAGE_VER=$(BASE_IMAGE_VER) --build-arg DEVC_ARCH=amd64 .

devc-arm64:
	docker build --file Dockerfile-devc --tag  effectiverange/er-devc-arm64-$(BASE_DISTRO)$(:)$(IMG_TAG) --build-arg BASE_IMAGE_REPO=effectiverange/arm64-$(BASE_DISTRO)-tools-base --build-arg BASE_IMAGE_VER=$(BASE_IMAGE_VER) --build-arg DEVC_ARCH=arm64 .

