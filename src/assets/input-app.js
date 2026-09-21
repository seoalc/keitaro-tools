(function() {
    'use strict';

    // ==========================================
    // 1. ГЕО ОПРЕДЕЛЕНИЕ (сначала!)
    // ==========================================
    let userCountryCode = null;
    let userDialCode = null;
    let geoDetected = false;
    let geoCallbacks = [];

    function getDialCode(countryCode) {
        const dialCodes = {
            'es': '34', 'mx': '52', 'ar': '54', 'co': '57', 'pe': '51',
            'cl': '56', 've': '58', 'ec': '593', 'gt': '502', 'cu': '53',
            'bo': '591', 'do': '1', 'hn': '504', 'py': '595', 'sv': '503',
            'ni': '505', 'cr': '506', 'pa': '507', 'uy': '598', 'pr': '1',
            'us': '1', 'ca': '1', 'uk': '44', 'fr': '33', 'de': '49',
            'it': '39', 'pt': '351', 'ru': '7', 'jp': '81', 'cn': '86',
            'au': '61', 'nz': '64', 'za': '27', 'br': '55', 'sa': '966',
            'ae': '971', 'eg': '20', 'ng': '234', 'pk': '92', 'bd': '880'
        };
        return dialCodes[countryCode.toLowerCase()] || '34';
    }

    function onGeoDetected(callback) {
        if (geoDetected) {
            callback(userCountryCode, userDialCode);
        } else {
            geoCallbacks.push(callback);
        }
    }

    function detectCountry() {
        console.log('🔍 Определение ГЕО...');

        fetch('https://ipapi.co/json/')
            .then(res => res.json())
            .then(data => {
                if (data && data.country_code) {
                    userCountryCode = data.country_code.toLowerCase();
                    userDialCode = data.country_calling_code || getDialCode(userCountryCode);
                    geoDetected = true;
                    console.log('✅ ГЕО определено через ipapi:', userCountryCode, userDialCode);
                    geoCallbacks.forEach(cb => cb(userCountryCode, userDialCode));
                    geoCallbacks = [];
                } else {
                    fallbackDetect();
                }
            })
            .catch(() => fallbackDetect());
    }

    function fallbackDetect() {
        console.log('🔄 Fallback: ipinfo...');
        fetch('https://ipinfo.io/json')
            .then(res => res.json())
            .then(data => {
                if (data && data.country) {
                    userCountryCode = data.country.toLowerCase();
                    userDialCode = getDialCode(userCountryCode);
                    geoDetected = true;
                    console.log('✅ ГЕО определено через ipinfo:', userCountryCode, userDialCode);
                    geoCallbacks.forEach(cb => cb(userCountryCode, userDialCode));
                    geoCallbacks = [];
                } else {
                    browserDetect();
                }
            })
            .catch(() => browserDetect());
    }

    function browserDetect() {
        console.log('🔄 Fallback: браузер...');
        const lang = navigator.language || 'en-US';
        const parts = lang.split('-');
        let code = parts.length > 1 ? parts[1].toLowerCase() : 'us';
        
        const langMap = { 
            'es': 'es', 'en': 'us', 'fr': 'fr', 'de': 'de', 
            'it': 'it', 'pt': 'pt', 'ru': 'ru'
        };
        const langCode = parts[0].toLowerCase();
        code = langMap[langCode] || code;
        
        if (langCode === 'es') {
            code = 'es';
        }
        
        userCountryCode = code;
        userDialCode = getDialCode(code);
        geoDetected = true;
        console.log('✅ ГЕО определено по браузеру:', userCountryCode, userDialCode);
        geoCallbacks.forEach(cb => cb(userCountryCode, userDialCode));
        geoCallbacks = [];
    }

    // Запускаем определение ГЕО сразу!
    detectCountry();

    // ==========================================
    // 2. ИНИЦИАЛИЗАЦИЯ ПОЛЕЙ (после ГЕО)
    // ==========================================
    function initPhoneFields() {
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', initFields);
        } else {
            initFields();
        }
    }

    function initFields() {
        const phoneInputs = document.querySelectorAll('.intgrtn-input.phonelist.phone-valid');
        if (!phoneInputs.length) {
            console.warn('⚠️ Поля телефона не найдены');
            return;
        }

        console.log('📱 Найдено полей телефона:', phoneInputs.length);

        // Ждём ГЕО перед инициализацией
        onGeoDetected(function(countryCode, dialCode) {
            console.log('🚀 Инициализация полей с кодом:', countryCode);
            phoneInputs.forEach(function(phoneInput) {
                initPhoneInput(phoneInput, countryCode);
            });
        });

        // Если ГЕО уже определилось (маловероятно, но на всякий случай)
        if (geoDetected) {
            console.log('🚀 Инициализация полей (ГЕО уже готово)');
            phoneInputs.forEach(function(phoneInput) {
                if (!phoneInput.__itiInitialized) {
                    initPhoneInput(phoneInput, userCountryCode);
                }
            });
        }
    }

    function updateHiddenFields(phoneInput, countryCode, dialCode) {
        const wrapper = phoneInput.closest('.phone-wrapper');
        if (!wrapper) return;
        
        const fullPhone = wrapper.querySelector('.full_phone');
        const countryCodeEl = wrapper.querySelector('[name="country_code"]');
        const phoneccEl = wrapper.querySelector('[name="phonecc"]');
        
        if (fullPhone) fullPhone.value = '';
        if (countryCodeEl) countryCodeEl.value = countryCode;
        if (phoneccEl) phoneccEl.value = dialCode;
    }

    // ========== ПОЗИЦИОНИРОВАНИЕ СПИСКА ==========
    function positionCountryList(countryList, selectedFlag) {
        if (!countryList || !selectedFlag) return;

        const flagRect = selectedFlag.getBoundingClientRect();
        const listHeight = countryList.offsetHeight || 300;
        const viewportHeight = window.innerHeight;
        const spaceBelow = viewportHeight - flagRect.bottom - 10;
        const spaceAbove = flagRect.top - 10;

        if (spaceBelow >= listHeight || spaceBelow >= spaceAbove) {
            countryList.style.top = (flagRect.bottom + window.pageYOffset) + 'px';
            countryList.style.bottom = 'auto';
            countryList.style.maxHeight = Math.min(300, spaceBelow - 10) + 'px';
        } else {
            countryList.style.bottom = (window.innerHeight - flagRect.top + window.pageYOffset) + 'px';
            countryList.style.top = 'auto';
            countryList.style.maxHeight = Math.min(300, spaceAbove - 10) + 'px';
        }

        const leftSpace = flagRect.left;
        const rightSpace = window.innerWidth - flagRect.right;
        const listWidth = countryList.offsetWidth || 320;

        if (leftSpace >= listWidth || leftSpace >= rightSpace) {
            countryList.style.left = flagRect.left + 'px';
            countryList.style.right = 'auto';
        } else {
            countryList.style.right = (window.innerWidth - flagRect.right) + 'px';
            countryList.style.left = 'auto';
        }
    }

    // ========== ИНИЦИАЛИЗАЦИЯ ОДНОГО ПОЛЯ ==========
    const itiInstances = [];

    function initPhoneInput(phoneInput, countryCode) {
        if (phoneInput.__itiInitialized) {
            return;
        }
        phoneInput.__itiInitialized = true;

        console.log('📱 Инициализация поля:', phoneInput.id || 'без id', 'страна:', countryCode);

        const iti = window.intlTelInput(phoneInput, {
            initialCountry: countryCode || 'es',
            separateDialCode: true,
            preferredCountries: ['es', 'mx', 'ar', 'co', 'pe', 'cl', 'us', 'ca'],
            utilsScript: 'https://cdnjs.cloudflare.com/ajax/libs/intl-tel-input/17.0.8/js/utils.js',
            autoPlaceholder: 'aggressive',
            formatOnDisplay: true,
            nationalMode: false,
            placeholderNumberType: 'MOBILE',
        });

        itiInstances.push(iti);

        const selectedFlag = phoneInput.closest('.iti').querySelector('.iti__selected-flag');
        
        if (selectedFlag) {
            selectedFlag.addEventListener('click', function(e) {
                setTimeout(function() {
                    const countryList = phoneInput.closest('.iti').querySelector('.iti__country-list');
                    if (countryList) {
                        positionCountryList(countryList, selectedFlag);
                    }
                }, 10);
            });

            selectedFlag.addEventListener('keydown', function(e) {
                if (e.key === 'Enter' || e.key === ' ') {
                    setTimeout(function() {
                        const countryList = phoneInput.closest('.iti').querySelector('.iti__country-list');
                        if (countryList) {
                            positionCountryList(countryList, selectedFlag);
                        }
                    }, 10);
                }
            });
        }

        function repositionList() {
            const countryList = phoneInput.closest('.iti').querySelector('.iti__country-list');
            if (countryList && countryList.style.display !== 'none') {
                positionCountryList(countryList, selectedFlag);
            }
        }

        window.addEventListener('scroll', repositionList, true);
        window.addEventListener('resize', repositionList);
        phoneInput.__reposition = repositionList;

        function validatePhone() {
            const value = phoneInput.value.trim();
            const wrapper = phoneInput.closest('.phone-wrapper');
            if (!wrapper) return true;

            const errorEl = wrapper.querySelector('.error-message');
            
            if (value.length === 0) {
                phoneInput.classList.remove('error', 'success');
                if (errorEl) errorEl.classList.remove('visible');
                return true;
            }

            const isValid = iti.isValidNumber();

            if (!isValid) {
                phoneInput.classList.remove('success');
                phoneInput.classList.add('error');
                if (errorEl) errorEl.classList.add('visible');
                return false;
            } else {
                phoneInput.classList.remove('error');
                phoneInput.classList.add('success');
                if (errorEl) errorEl.classList.remove('visible');
                
                const fullNumber = iti.getNumber();
                const fullPhoneEl = wrapper.querySelector('.full_phone');
                if (fullPhoneEl) fullPhoneEl.value = fullNumber;

                const countryData = iti.getSelectedCountryData();
                updateHiddenFields(phoneInput, countryData.iso2, countryData.dialCode);
                return true;
            }
        }

        phoneInput.addEventListener('countrychange', function() {
            const countryData = iti.getSelectedCountryData();
            updateHiddenFields(phoneInput, countryData.iso2, countryData.dialCode);
            validatePhone();
        });

        phoneInput.addEventListener('input', validatePhone);
        phoneInput.addEventListener('blur', validatePhone);

        phoneInput.__validate = validatePhone;

        setTimeout(validatePhone, 500);

        return iti;
    }

    // ========== ОБРАБОТЧИКИ ФОРМ ==========
    function setupFormHandlers() {
        const forms = document.querySelectorAll('form');
        forms.forEach(function(form) {
            const formPhoneInputs = form.querySelectorAll('.intgrtn-input.phonelist.phone-valid');
            if (!formPhoneInputs.length) return;

            const originalSubmit = form.onsubmit;

            form.onsubmit = function(e) {
                let allValid = true;

                formPhoneInputs.forEach(function(phoneInput) {
                    if (phoneInput.__validate) {
                        const isValid = phoneInput.__validate();
                        if (!isValid) {
                            allValid = false;
                            phoneInput.focus();
                        }
                    }
                });

                if (!allValid) {
                    e.preventDefault();
                    e.stopPropagation();
                    return false;
                }

                if (typeof originalSubmit === 'function') {
                    return originalSubmit.call(this, e);
                }

                return true;
            };

            const submitBtns = form.querySelectorAll('[type="submit"]');
            submitBtns.forEach(function(btn) {
                btn.addEventListener('click', function(e) {
                    let allValid = true;

                    formPhoneInputs.forEach(function(phoneInput) {
                        if (phoneInput.__validate) {
                            const isValid = phoneInput.__validate();
                            if (!isValid) {
                                allValid = false;
                                phoneInput.focus();
                            }
                        }
                    });

                    if (!allValid) {
                        e.preventDefault();
                        e.stopPropagation();
                        return false;
                    }
                });
            });
        });
    }

    // ==========================================
    // 3. ЗАПУСК
    // ==========================================
    initPhoneFields();

    // Ждём загрузки DOM для обработчиков форм
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', setupFormHandlers);
    } else {
        setupFormHandlers();
    }

    // Форс-инициализация если что-то пошло не так (через 5 секунд)
    setTimeout(function() {
        const phoneInputs = document.querySelectorAll('.intgrtn-input.phonelist.phone-valid');
        phoneInputs.forEach(function(phoneInput) {
            if (!phoneInput.__itiInitialized) {
                console.warn('⚠️ Форс-инициализация поля:', phoneInput);
                const country = userCountryCode || 'es';
                initPhoneInput(phoneInput, country);
            }
        });
    }, 5000);

    window.__phoneInputsES = {
        instances: itiInstances,
        geoDetected: geoDetected,
        userCountryCode: userCountryCode
    };

})();