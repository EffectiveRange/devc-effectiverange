BASE_IMAGE_REPO=effectiverange/armhf-bookworm-tools-base
BASE_IMAGE_VER=latest
colon := :
$(colon) := :
TEST_FILES := $(wildcard *.sh)
TESTS := $(TEST_FILES:.sh=.test)
ifeq ($(USER),root)
    USERNAME := testuser
else
    USERNAME := $(USER)
endif

test: build_test_image  $(TESTS)

build_test_image:
	docker build    --rm -t devctestimage --build-arg BASE_IMAGE_REPO=$(BASE_IMAGE_REPO) \
					--build-arg BASE_IMAGE_VER=$(BASE_IMAGE_VER) \
					--build-arg USERNAME=$(USERNAME) .

%.test: %.sh
	docker run --privileged -u $(USERNAME) devctestimage  /home/$(USERNAME)/test/$<
	touch $@


clean:
	rm -f $(TESTS)


.PHONY: test build_test_image 