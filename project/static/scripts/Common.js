const BASE_URL = 'http://192.168.1.79:8000';
// const BASE_URL = 'http://127.0.0.1:8000';
const token = '';

const CASTER = {
    id: 137,
    last_name: 'BENETO',
    first_name: 'Natacha'
};

var API = {
    get: function (url) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}${url}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    post: function (url, payload) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `${BASE_URL}${url}`,
                method: 'POST',
                data: JSON.stringify(payload),
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    response = JSON.parse(err.responseText);
                    reject(response);
                }
            });
        });
    },


    getSiblings: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/v1/siblings/child/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getRecord: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/v1/records/child/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getUserById: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getChild: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getChildren: function() {
        return new Promise(function(resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/children/`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        }) 
    },


    getParent: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getParents: function () {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/parents/`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getClients: function () {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/users/clients/`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getProducts: function () {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/v1/params/details`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getRecord: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/v1/records/child/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    getTickets: function (id) {
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${BASE_URL}/v1/order/child/${id}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        })
    },


    postClient: function (payload) {
        console.log(payload);
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `${BASE_URL}/users/clients/`,
                method: 'POST',
                data: JSON.stringify(payload),
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        });
    },


    _verifyOrder: function (payload) {
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `${BASE_URL}/v1/order/create`,
                method: 'POST',
                data: JSON.stringify(payload),
                headers: {
                    Authorization: `Bearer ${token}`,
                },
                success: function (data) {
                    resolve(data);
                },
                error: function (err) {
                    reject(err);
                }
            });
        });
    },


    getTicketsByChild: function(id) {
        const url = `/v1/order/child/${id}`;
        return this.get(url);
    },

    getOrderById: function (id) {
        const url = `/v1/order/${id}`;
        return this.get(url);
    },

    verifyOrder: function (payload) {
        const url = '/v1/order/verify';
        return this.post(url, payload);
    },


    confirmOrder: function (payload) {
        const url = '/v1/order/confirm';
        return this.post(url, payload);
    },
};


var UI = {

    createList: function(id, list, onClick = undefined, onDblClick = undefined) {
        const element = document.getElementById(id);
        const list_group = element.querySelector('.list-group');

        list_group.innerHTML = '';

        for (var i = 0; i < list.length; ++i) {
            var li = document.createElement('li')
            li.className = 'list-group-item';
            li.setAttribute('data-index', i);

            li.addEventListener('click', onClick);
            li.addEventListener('dblclick', onDblClick);

            li.innerHTML = `#${list[i].id} - ${list[i].first_name} ${list[i].last_name} ${(list[i].dob) ? ' - ' + list[i].dob : ''}`;

            list_group.appendChild(li);
        }
    },


    createListParent: function (id, list, onClick = undefined, onDblClick = undefined) {
        const element = document.getElementById(id);
        const list_group = element.querySelector('.list-group');

        list_group.innerHTML = '';

        if (Array.isArray(list)) {

            for (var i = 0; i < list.length; ++i) {
                var li = document.createElement('li')
                    li.className = 'list-group-item';
                    li.setAttribute('data-index', i);
        
                    li.addEventListener('click', onClick);
                    li.addEventListener('dblclick', onDblClick);
        
                    li.innerHTML = `#${list[i].id} - ${list[i].first_name} ${list[i].last_name} - ${list[i].roles[0].name}`;
    
                list_group.appendChild(li);
            }
        }
        else {
            var li = document.createElement('li')
                li.className = 'list-group-item';
                li.setAttribute('data-index', i);

                li.addEventListener('click', onClick);
                li.addEventListener('dblclick', onDblClick);

                li.innerHTML = `#${list.id} - ${list.first_name} ${list.last_name} - ${list.roles[0].name}`;

            list_group.appendChild(li);
        }

    },


    createWrapper: function (title, content) {
        var wrapper = document.createElement('div');
            wrapper.className = 'wrapper';

        var _title = document.createElement('div');
            _title.className = 'wrapper-title';

        var p = document.createElement('p');
            p.className = 'title';
            p.innerHTML = title;

        title.appendChild(p);

        wrapper.appendChild(_title);
        wrapper.appendChild(content);

        return wrapper;
    },


    createRecord: function() {

    },


    createProduct: function(type, product) {
        return `<li class="product-tile ${type}" data-id="${product.id}">
            <div class="product-tile-head">
                <div class="product-meta-title">${product.name}</div>
            </div>
        
            <div class="product-tile-body">
                <div class="product-meta-add"><i class="fas fa-plus"></i></div>
                <div class="product-meta-ban"><i class="fas fa-ban"></i></div>
                <div class="product-meta-check"><i class="fas fa-check"></i></div>
                <div class="product-meta-selected"><i class="fas fa-cart-arrow-down"></i></div>
                <div class="product-meta-checkbox"><input type="checkbox" onclick=""/></div>
            </div>
        
            <div class="product-tile-footer">
                <div class="product-meta-price">${product.price} E</div>
                <div class="product-meta-bought">payé le <span></span></div>
            </div>
        </li>`;
    },


    


    Products: {
        CATEGORY: [
            '',
            'PERI',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'AVRIL',
            'MAI',
            'JUIN',
            'JUILLET',
            'AOUT',
            'SEPTEMBRE',
            'OCTOBRE',
            'NOVEMBRE',
            'DECEMBRE',
            'TOUSSAINT',
            'NOEL',
            'CARNAVAL',
            'PAQUES',
            'GRDS_VACANCES_JUILLET',
            'GRDS_VACANCES_AOUT',
        ],


        ui_create_products: function(products, alsh=true) {
            let _peri = [];
            let _alsh = {};

            for (var i = 0; i < products.length; ++i) {
                if (products[i]['category'] === 1) {
                    _peri.push(products[i]);
                }
                else {
                    const c = this.CATEGORY[products[i]['category']];

                    if (!_alsh[c])
                        _alsh[c] = [];
                    _alsh[c].push(products[i]);
                }
            }

            var m6 = '';
            var p6 = '';

            m6, p6 += this.ui_create_products_peri(_peri);
            if (alsh) {
                const tmp = this.ui_create_products_alsh(_alsh);
                m6 += tmp['m6'];
                p6 += tmp['p6'];
            }

            return {
                'snippet_m6': m6,
                'snippet_p6': p6,
            };
        },


        ui_create_products_peri: function(peri) {
            let snippet = '';
            for (var i = 0; i < peri.length; ++i) {
                snippet += UI.createProduct('normal', peri[i]);
            }
            return `<li class="product-category">
                <h3 class="product-category-title">PERI</h3>
                <ul class="product-category-products">${snippet}</ul>
            </li>`;
        },    


        ui_create_products_alsh: function(alsh) {
            let snippet = '';
            let m6 = '';
            let p6 = '';
            Object.keys(alsh).forEach((item) => {
                snippet = this.ui_create_products_alsh_(item, alsh[item]);
                m6 += snippet['m6'];
                p6 += snippet['p6'];
            });
            return {'m6': m6, 'p6': p6};
        },


        ui_create_products_alsh_: function(period, products) {
            let m6 = '';
            let p6 = '';
            for (var i = 0; i < products.length; ++i) {
                if (products[i]['subcategory'] === 1)
                    m6 += `<li class="product-category-product">${UI.createProduct('normal', products[i])}</li>`;
                else
                    p6 += `<li class="product-category-product">${UI.createProduct('normal', products[i])}</li>`;
            }
            return {
                'm6': `<li class="product-category">
                            <h3 class="product-category-title">${period}</h3>
                            <ul class="product-category-products">${m6}</ul>
                        </li>`,
                
                'p6': `<li class="product-category">
                            <h3 class="product-category-title">${period}</h3>
                            <ul class="product-category-products">${p6}</ul>
                        </li>`
            };
        },


        ui_products_init: function(onClick) {
            document
                .querySelectorAll('#tabs-body .product-tile')
                .forEach((item) => {
                    item.addEventListener('click', function(e) {
                        e.preventDefault();

                        let target = e.target;
                        while (!target.classList.contains('product-tile')) {
                            target = target.parentElement;
                        }

                        const product_id = target.getAttribute('data-id');
                        const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');
                        
                        onClick(child_id, product_id);
                    });
                });
        },


        ui_products_item_onClick: function(e) {
            e.preventDefault();

            let target = e.target;
            while (!target.classList.contains('product-tile')) {
                target = target.parentElement;
            }

            if (target.classList.contains('main') ||
                target.classList.contains('summary') ||
                target.classList.contains('expired') ||
                target.classList.contains('breaking') ||
                target.classList.contains('purchased')) {
                return;
            }

            const child_id = target.parentElement.getAttribute('data-id');
            const product_id = target.getAttribute('data-id');

            console.log(child_id);
            console.log(product_id);

            switch (cart_toggleItem(product_id, child_id)) {
                case 0:
                    break;

                case 1:
                    target.className = 'product-tile normal';
                    break;

                case 2:
                    target.className = 'product-tile selected';
                    break;
            }
        },
    },


    Tabs: {
        ui_tabs_init: function() {
            document
                .querySelectorAll('#tabs-header .tabs-header-item')
                .forEach((item) => {
                    item.addEventListener('click', this.ui_tabs_header_item_onClick);
                });
        },


        ui_tabs_header_item_onClick: function(e) {
            const index = e.target.getAttribute('data-index');

            // Remove old styles
            document.querySelector('#tabs-header .tabs-header-item.active').classList.remove('active');

            document.querySelector('#tabs-body .tabs-body-child.active').classList.remove('active');
            
            // Add new styles
            e.target.classList.add('active');
            
            document.querySelector(`#tabs-body .tabs-body-child[data-index="${index}"]`).classList.add('active');
        },

        
        // Build tabs header
        ui_tabs_header: function(children) {
            const group = document.querySelector('#tabs-header .tabs-header-group');

            group.innerHTML += this.ui_tabs_header_item(0, children[0], true);
            for (var i = 1; i < children.length; ++i) {
                group.innerHTML += this.ui_tabs_header_item(i, children[i]);
            }
        },


        // Build tabs header item
        // li - data-index - data-id
        ui_tabs_header_item: function(index, child, active = false) {
            return `<li data-index="${index}" data-id="${child['id']}" class="tabs-header-item ${(active) ? 'active' : ''}">${child['first_name']}</li>`;
        },


        ui_tabs_body: function(children) {
            const group = document.querySelector('#tabs-body .tabs-body-children');

            group.appendChild(this.ui_tabs_body_child(0, children[0], true));
            for (var i = 1; i < children.length; ++i) {
                group.appendChild(this.ui_tabs_body_child(i, children[i]));
            }
        },


        // Build tabs header item
        // li - data-index - data-id
        ui_tabs_body_child: function(index, child, active = false) {

            var products_ul = document.createElement('ul');
                products_ul.className = 'tabs-body-child-products';
                products_ul.setAttribute('data-id', child['id']);
                products_ul.setAttribute('data-index', index);

            var record_ul = document.createElement('ul');
                record_ul.className = 'tabs-body-child-record';
                record_ul.innerHTML = this.ui_tabs_body_child_record();
            
            var wrapper_content = document.createElement('div');
                wrapper_content.className = 'wrapper-content';

                wrapper_content.appendChild(record_ul);
                wrapper_content.appendChild(products_ul);
            
            var title = document.createElement('p');
                title.className = 'title';
                title.innerHTML = child['first_name'];

            var wrapper_title = document.createElement('div');
                wrapper_title.className = 'wrapper-title';

                wrapper_title.appendChild(title);

            var wrapper = document.createElement('div');
                wrapper.className = 'wrapper';

                wrapper.appendChild(wrapper_title);
                wrapper.appendChild(wrapper_content);
            
            var li = document.createElement('li');
                li.className = 'tabs-body-child ' + ((active) ? 'active' : '');
                li.setAttribute('data-index', index);

                li.appendChild(wrapper);
                
            return li;
        },
        

        ui_tabs_body_child_record: function() {
            return `<li><b>Ecole: </b>          <span class="record-school"></span></li>
                    <li><b>Classe: </b>         <span class="record-classroom"</span></li>
                    <li><b>Quotient 2019: </b>  <span class="record-quotient-q1"</span></li>
                    <li><b>Quotient 2020: </b>  <span class="record-quotient-q2"</span></li>`;
        },


        ui_update_records: function(children) {
            for (var i = 0; i < children.length; ++i) {
                const child = children[i];

                const tabs_body_record = document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-record`);

                const classroom = Utils.RECORD_CLASSROOM[child['record']['classroom']];
                const quotient_q1 = Utils.RECORD_QUOTIENT[child['record']['caf']['quotient_q1']];
                const quotient_q2 = Utils.RECORD_QUOTIENT[child['record']['caf']['quotient_q2']];

                tabs_body_record.querySelector(`.record-school`).innerHTML = child['record']['school'];
                tabs_body_record.querySelector(`.record-classroom`).innerHTML = classroom;
                tabs_body_record.querySelector(`.record-quotient-q1`).innerHTML = quotient_q1;
                tabs_body_record.querySelector(`.record-quotient-q2`).innerHTML = quotient_q2;
            }

        },


        ui_update_products: function(children, snippets) {
            for (var i = 0; i < children.length; ++i) {
                if (children[i]['record']['classroom'] >= 1 &&
                    children[i]['record']['classroom'] <= 4) {
                    
                        document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-products`).innerHTML = snippets['snippets_m6'];
                }
                else if (children[i]['record']['classroom'] >= 5 &&
                    children[i]['record']['classroom'] <= 9) {

                    document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-products`).innerHTML = snippets['snippets_p6'];
                }
                else {
                    console.log(`Error: Unknow classroom (${children[i]['record']['classroom']}) for child: ${children[i]['first_name'] + ' ' + children[i]['last_name']}`);
                }
            }
        },
    },
};


var Utils = {
    RECORD_QUOTIENT: [
        '',
        'NE',
        'Q2',
        'Q1',
    ],

    RECORD_CLASSROOM: [
        'UNSET',
        'STP',
        'SP',
        'SM',
        'SG',
        'CP',
        'CE1',
        'CE2',
        'CM1',
        'CM2',
    ],

    ORDER_STATUS: {
        'UNSET':        0,
        'PENDING':      1,
        'CANCELED':     2,
        'COMPLETED':    3,
        'REFUNDED':     4,
    },

    ORDER_METHOD: {
        'UNSET':    0,
        'CASH':     1,
        'CHECK':    2,
        'ONLINE':   3,
        'VRMT':     4,
    },


    capitalize: function(str) {
        var _str = str.slice(1).toLowerCase();
        return str[0].toUpperCase() + _str;
    },

    normalize: function(str) {
        return str.normalize("NFD").replace(/[\u0300-\u036f]/g, "");
    },


    filterItems: function(list, filter) {
        if (filter === '' ||
            filter.length < 3)
            return list;

        let list_filtered = [];
        
        var _filter = filter.toLowerCase();
            _filter = _filter.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

        for (var i = 0; i < list.length; ++i) {
            var inner = `#${list[i].id} - ${list[i].first_name} ${list[i].last_name} ${(list[i].dob) ? '- ' + list[i].dob : ''}`;
                inner = inner.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            
            if (inner.includes(_filter)) 
                list_filtered.push(list[i]);
        }

        return list_filtered;
    },


    filterItemsParents: function (list, filter) {
        if (filter === '' ||
            filter.length < 3)
            return list;

        let list_filtered = [];

        var _filter = filter.toLowerCase();
        _filter = _filter.normalize("NFD").replace(/[\u0300-\u036f]/g, "");

        for (var i = 0; i < list.length; ++i) {
            var inner = `#${list[i].id} - ${list[i].first_name} ${list[i].last_name}`;
            inner = inner.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

            if (inner.includes(_filter))
                list_filtered.push(list[i]);
        }

        return list_filtered;
    },
    
    
    test_email: function(email) {
        return /^\w+([\.-]?\w+)*@\w+([\.-]?\w+)*(\.\w{2,3})+$/.test(email);
    },

    test_phone: function(phone) {
        var _phone = phone.replace(/ /g, '');

        if (!/^[+]?[\d]*$/.test(_phone))
            return false;
            
        if (_phone[0] === '+') {
            if (_phone.length !== 13)
                return false;
        }
        else {
            if (_phone.length !== 10)
                return false;
        }
        return true;
    },


    Products: {
        CATEGORY: [
            '',
            'PERI',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'AVRIL',
            'MAI',
            'JUIN',
            'JUILLET',
            'AOUT',
            'SEPTEMBRE',
            'OCTOBRE',
            'NOVEMBRE',
            'DECEMBRE',
            'TOUSSAINT',
            'NOEL',
            'CARNAVAL',
            'PAQUES',
            'GRDS_VACANCES_JUILLET',
            'GRDS_VACANCES_AOUT',
        ],


        order: function (products, alsh = true) {
            let _peri = [];
            let _alsh_m6 = {};
            let _alsh_p6 = {};

            for (var i = 0; i < products.length; ++i) {
                if (products[i]['category'] === 1) {
                    _peri.push(products[i]);
                }
                else {
                    const c = this.CATEGORY[products[i]['category']];

                    if (products[i]['subcategory'] === 1) {
                        if (!_alsh_m6[c])
                            _alsh_m6[c] = [];
                        _alsh_m6[c].push(products[i]);
                    }
                    else if (products[i]['subcategory'] === 2) {
                        if (!_alsh_p6[c])
                            _alsh_p6[c] = [];
                        _alsh_p6[c].push(products[i]);
                    }
                }
            }

            const peri = this.order_peri(_peri);

            if (alsh) {
                const m6 = this.order_alsh(_alsh_m6);
                const p6 = this.order_alsh(_alsh_p6);

                return {
                    'snippet_m6': peri + m6,
                    'snippet_p6': peri + p6,
                };
            }
            else {
                return {
                    'snippet_m6': peri,
                    'snippet_p6': peri,
                };
            }

        },


        order_peri: function (peri) {
            let snippet = '';
            for (var i = 0; i < peri.length; ++i) {
                snippet += UI.createProduct('normal', peri[i]);
            }
            return `<li class="product-category">
                <h3 class="product-category-title">PERI</h3>
                <ul class="product-category-products">${snippet}</ul>
            </li>`;
        },


        order_alsh: function (alsh) {
            let snippet = '';
            Object.keys(alsh).forEach((item) => {
                snippet += this.order_alsh_period(item, alsh[item]);
            });
            return snippet;
        },


        order_alsh_period: function (period, products) {
            let snippet = '';
            for (var i = 0; i < products.length; ++i) {
                snippet += `<li class="product-category-product">${UI.createProduct('normal', products[i])}</li>`;
            }
            return `<li class="product-category">
                        <h3 class="product-category-title">${period}</h3>
                        <ul class="product-category-products">${snippet}</ul>
                    </li>`;
        },


        ui_products_init: function (onClick) {
            document
                .querySelectorAll('#tabs-body .product-tile')
                .forEach((item) => {
                    item.addEventListener('click', function (e) {
                        e.preventDefault();

                        let target = e.target;
                        while (!target.classList.contains('product-tile')) {
                            target = target.parentElement;
                        }

                        const product_id = target.getAttribute('data-id');
                        const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');

                        onClick(child_id, product_id);
                    });
                });
        },


        ui_products_item_onClick: function (e) {
            e.preventDefault();

            let target = e.target;
            while (!target.classList.contains('product-tile')) {
                target = target.parentElement;
            }

            if (target.classList.contains('main') ||
                target.classList.contains('summary') ||
                target.classList.contains('expired') ||
                target.classList.contains('breaking') ||
                target.classList.contains('purchased')) {
                return;
            }

            const child_id = target.parentElement.getAttribute('data-id');
            const product_id = target.getAttribute('data-id');

            console.log(child_id);
            console.log(product_id);

            switch (cart_toggleItem(product_id, child_id)) {
                case 0:
                    break;

                case 1:
                    target.className = 'product-tile normal';
                    break;

                case 2:
                    target.className = 'product-tile selected';
                    break;
            }
        },
    },

    orderDate: function(_date) {
        var d = new Date(_date);
        const x = d.toISOString().split('T');
        const y = x[1].split('.');
        return x[0] + ' ' + y[0];
    }
};


/**
 * Render a set of controls according to a state
 *  states
 *      - Children
 *      - Parent
 *      - Shop
 *      - Summary
 *      - Payment
 *      - Receipt
 */
var Controls = {

    render: function (e, state) {
        var items_selected = '<div class=""><p><span class="controls-items_selected"></span> produit(s) sélectionné(s)</p></div>';

        let button_cancel = '<button class="controls-cancel btn btn-danger">Annuler</button>';
        let button_submit = '<button class="controls-submit btn btn-success">Valider(<span class="controls-amount"></span> E)</button >';
        let button_previous = '<button class="controls-previous btn btn-warning">Retour</button>';
        let button_continue = '<button class="controls-continue btn btn-success">Continuer</button>';
        let button_pay = '<button class="controls-pay btn btn-success">Payer(<span class="controls-amount"></span> E)</button>';

        switch (state) {
            case 'Children':
                button_pay = '';
                button_submit = '';
                button_previous = '';

                items_selected = '';
                break;

            case 'Parent':
                button_pay = '';
                button_submit = '';

                items_selected = '';
                break;

            case 'Shop':
                button_pay = '';
                button_continue = '';
                break;

            case 'Summary':
                button_submit = '';
                button_continue = '';
                break;

            case 'Payment':
                button_cancel = '';
                button_submit = '';
                button_previous = '';
                button_continue = '';

                items_selected = '';
                break;

            case 'Receipt':
                button_cancel = '';
                button_submit = '';
                button_previous = '';
                button_continue = '';

                items_selected = '';
                break;
        }

        var controls = document.createElement('div');
            controls.className = 'Controls';
            controls.innerHTML = `<div class="Controls-texts col-6">
                                    ${items_selected}
                                </div>
                                <div class="Controls-buttons col-6">
                                    ${button_cancel}
                                    ${button_previous}
                                    ${button_continue}
                                    ${button_submit}
                                    ${button_pay}
                                </div>
                                <div class="Controls-buttons col-12">
                                    <div class="Controls-alert alert alert-danger" role="alert"></div>
                                </div>`;

        e.appendChild(controls);
    },


    updateEvents: function (
        e,
        state,
        cancel_onClick = null,
        continue_onClick = null,
        previous_onClick = null,
        submit_onClick = null,
        pay_onClick = null
    ) {
        let self = this;

        var pay_ = e.querySelector('.controls-pay');
        if (pay_) {
            pay_.addEventListener('click', function (e) {
                // self._pay_onClick(state, e);
                if (pay_onClick)
                    pay_onClick(e);
            });
        }

        var cancel = e.querySelector('.controls-cancel');
        if (cancel) {
            cancel.addEventListener('click', function (e) {
                console.log(this);
                // self._cancel_onClick(state, e);
                if (cancel_onClick)
                    cancel_onClick(e);
            });
        }

        var submit = e.querySelector('.controls-submit');
        if (submit) {
            submit.addEventListener('click', function (e) {
                // self._submit_onClick(state, e);
                if (submit_onClick)
                    submit_onClick(e);
            });
        }

        var previous = e.querySelector('.controls-previous');
        if (previous) {
            previous.addEventListener('click', function (e) {
                // self._previous_onClick(state, e);
                if (previous_onClick)
                    previous_onClick(e);
            });
        }

        var continue_ = e.querySelector('.controls-continue');
        if (continue_) {
            continue_.addEventListener('click', function (e) {
                // self._continue_onClick(state, e);
                if (continue_onClick)
                    continue_onClick(e);
            });
        }
    },

    
    updateItemsSelected: function (e, count) {
        e.querySelector('.controls-items_selected').innerHTML = count;
    },


    updateAmount: function (e, amount) {
        e.querySelector('.controls-amount').innerHTML = amount;
    },


    showAlert: function (e) {
        e.querySelector('.Controls-alert').classList.add('show');
    },


    hideAlert: function (e) {
        e.querySelector('.Controls-alert').classList.remove('show');
    },


    updateAlert: function(e, msg) {
        e.querySelector('.Controls-alert').innerHTML = msg;
    },
};


/**
 * Render a simple search bar
 */
var Search = {

    render: function(e) {
        e.innerHTML += `<div class="Search">
                            <input class="form-control" type="text" placeholder="Search" aria-label="Search">
                        </div>`;
    },
};


/**
 * List used in Children
 * list a set of children
 */
var List = {

    render: function(e) {
        e.innerHTML += `<div class="List">
                            <div class="List-selected">
                                <p>Sélectionné(s)</p>

                                <ul class="list-group">
                                </ul>
                            </div>

                            <div class="List-items">
                                <p>Elément(s)</p>

                                <ul class="list-group">
                                </ul>
                            </div>
                        </div>`;
    },


    setActive: function(e, id) {
        e.querySelectorAll('.List-items .list-group li').forEach((item) => {
            
        });
    },


    updateList: function(e, children, onClick=null, onDblClick=null) {
        var List = e.querySelector('.List-items .list-group');

        for (var i = 0; i < children.length; ++i) {
            var li = document.createElement('li')
                li.className = 'list-group-item';
                li.setAttribute('data-index', i);

                li.addEventListener('click', onClick);
                li.addEventListener('dblclick', onDblClick);

                li.innerHTML = `#${children[i].id} - ${children[i].first_name} ${children[i].last_name} ${(children[i].dob) ? ' - ' + children[i].dob : ''}`;

                List.appendChild(li);
        }
    },


    updateFilteredList: function (e, filter) {
        e.querySelectorAll('.List-items .list-group li').forEach((item) => {
            var _item = item.innerHTML.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
            var _filter = filter.toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");

            console.log(_item);
            if (!_item.includes(_filter))
                item.classList.add('hide');
            else
                item.classList.remove('hide');
        });
    },


    updateSelected: function(e, child, onClick=null) {
        var List = e.querySelector('.List-selected .list-group');

        var li = document.createElement('li')
            li.className = 'list-group-item';

            li.addEventListener('click', onClick);

            li.innerHTML = `#${child.id} - ${child.first_name} ${child.last_name} ${(child.dob) ? ' - ' + child.dob : ''}`;

        List.appendChild(li);
    },


    resetSelected: function(e) {
        e.querySelector('.List-selected .list-group').innerHTML = '';
    },


    resetItems: function(e) {
        e.querySelectorAll('.List-items .list-group .active')
            .forEach((item) => {
                item.classList.remove('active');
            });
    },


    resetFilteredList: function(e) {
        e.querySelectorAll('.List-items .list-group .hide').forEach((item) => {
            item.classList.remove('hide');
        });
    }
};


/**
 *  Tabs used in Shop
 */
var Tabs = {
    render: function(e, children, products) {

        e.innerHTML = `<div class="Tabs">
                        <div class="Tabs-header">
                            <div class="Tabs-header-dir">
                                <input type="checkbox" />
                                <input type="text" />
                            </div>
                            <ul class="Tabs-header-group"></ul>
                        </div>
                        <div class="Tabs-body">
                            <ul class="Tabs-body-children"></ul>
                        </div>
                       </div>`;

        // Render header
        // And events
        this.render_header(e, children);

        this.render_body(e, children, products);

        this.updateChildrenTickets(e, children);
    },


    render_header: function (e, children) {
        const group = e.querySelector('.Tabs-header-group');


        group.innerHTML += this.render_header_item(0, children[0], true);
        for (var i = 1; i < children.length; ++i) {
            group.innerHTML += this.render_header_item(i, children[i]);
        }

        // Add Events
        e.querySelectorAll('.Tabs-header-item')
        .forEach((item) => {
            item.addEventListener('click', this.renderHeader_onClick);
        });
    },


    render_header_item: function (index, child, active=false) {
        return `<li data-index="${index}" data-id="${child['id']}" class="Tabs-header-item ${(active) ? 'active' : ''}">${child['first_name']}</li>`;
    },


    renderHeader_onClick: function (e) {
        const index = e.target.getAttribute('data-index');

        // Remove old styles
        document.querySelector('.Tabs-header-item.active').classList.remove('active');

        document.querySelector('.Tabs-body-child.active').classList.remove('active');

        // Add new styles
        e.target.classList.add('active');

        document.querySelector(`.Tabs-body-child[data-index="${index}"]`).classList.add('active');
    },


    render_body: function(e, children, products) {
        const group = e.querySelector('.Tabs-body-children');

        // Get products HTML
        let snippet = '';
        const snippets = Utils.Products.order(products);

        
        // Render 1st child as active
        if (children[0]['record']['classroom'] >= 1 &&
            children[0]['record']['classroom'] <= 4) {
            snippet = snippets['snippet_m6'];
        }
        else {
            snippet = snippets['snippet_p6'];
        }

        group.appendChild(this.render_body_item(0, children[0], snippet, true));
        
        // Render rest of children
        for (var i = 1; i < children.length; ++i) {
            if (children[i]['record']['classroom'] >= 1 &&
                children[i]['record']['classroom'] <= 4) {
                snippet = snippets['snippet_m6'];
            }
            else {
                snippet = snippets['snippet_p6'];
            }

            group.appendChild(this.render_body_item(i, children[i], snippet));
        }
    },


    render_body_item: function(index, child, products, active=false) {
        var products_ul = document.createElement('ul');
            products_ul.innerHTML = products;
            products_ul.className = 'Tabs-body-child-products';
            products_ul.setAttribute('data-id', child['id']);
            products_ul.setAttribute('data-index', index);

        var record_ul = document.createElement('ul');
            record_ul.className = 'Tabs-body-child-record';
            record_ul.innerHTML = this.render_record(child['record']);

        var wrapper_content = document.createElement('div');
            wrapper_content.className = 'wrapper-content';

            wrapper_content.appendChild(record_ul);
            wrapper_content.appendChild(products_ul);

        var title = document.createElement('p');
            title.className = 'title';
            title.innerHTML = child['first_name'];

        var wrapper_title = document.createElement('div');
            wrapper_title.className = 'wrapper-title';

            wrapper_title.appendChild(title);

        var wrapper = document.createElement('div');
            wrapper.className = 'wrapper';

            wrapper.appendChild(wrapper_title);
            wrapper.appendChild(wrapper_content);

        var li = document.createElement('li');
            li.className = 'Tabs-body-child ' + ((active) ? 'active' : '');
            li.setAttribute('data-index', index);

            li.appendChild(wrapper);

        return li;
    },


    render_record: function (record) {
        const classroom = Utils.RECORD_CLASSROOM[record['classroom']];
        const quotient_q1 = Utils.RECORD_QUOTIENT[record['caf']['quotient_q1']];
        const quotient_q2 = Utils.RECORD_QUOTIENT[record['caf']['quotient_q2']];

        return `<li><b>Ecole: </b>          <span class="record-school">        ${record['school']}</span></li>
                <li><b>Classe: </b>         <span class="record-classroom">     ${classroom}</span></li>
                <li><b>Quotient 2019: </b>  <span class="record-quotient-q1">   ${quotient_q1}</span></li>
                <li><b>Quotient 2020: </b>  <span class="record-quotient-q2">   ${quotient_q2}</span></li>`;
    },


    updateChildrenTickets: function(e, children) {
        for (let i in children) {
            const child = children[i];
            const tab = e.querySelector(`.Tabs-body-child-products[data-id="${child.id}"]`);

            if ('tickets' in child) {

                for (let j in child['tickets']) {
                    const ticket = child['tickets'][j];

                    // Error check
                    if (!ticket['product'])
                        continue;

                    // Find last status
                    let d = null;
                    let s = null;
                    for (let k in ticket['status']) {
                        const status = ticket['status'][k];

                        if (!d) {
                            s = status.status;
                            d = new Date(status.date);
                            continue;
                        }

                        const d2 = new Date(status.date);

                        if (d2 > d) {
                            d = d2;
                            s = status.status;
                        }
                    }

                    if (!d)
                        continue;

                    let className = 'normal';
                    if (s === 2)
                        className = 'purchased';
                    
                    // Remove old style
                    // Add purchased style
                    console.log(ticket.product);
                    const product = tab.querySelector(`.product-tile[data-id="${ticket.product}"]`);

                    if (!product) {
                        console.log('updateChildrenTickets() - Failed to get element for product ID: ' + ticket.product);
                        continue;
                    }
                    product.classList.add(className);
                    product.classList.remove('normal');

                    // Add purchased date
                    product.querySelector('.product-meta-bought span').innerHTML = d.toJSON().split('T')[0];
                }
            }
        }
    },


    updateBodyEvents: function (e, onClick) {
        e
            .querySelectorAll('.Tabs-body .product-tile')
            .forEach((item) => {
                item.addEventListener('click', function (e) {
                    e.preventDefault();

                    let target = e.target;
                    while (!target.classList.contains('product-tile')) {
                        target = target.parentElement;
                    }

                    const product_id = target.getAttribute('data-id');
                    const child_id = target.parentElement.parentElement.parentElement.getAttribute('data-id');

                    onClick(child_id, product_id);
                });
            });
    },
        
    


    // Useless
    updateRecord: function(children) {
        for (var i = 0; i < children.length; ++i) {
            const child = children[i];

            const tabs_body_record = document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-record`);

            const classroom = Utils.RECORD_CLASSROOM[child['record']['classroom']];
            const quotient_q1 = Utils.RECORD_QUOTIENT[child['record']['caf']['quotient_q1']];
            const quotient_q2 = Utils.RECORD_QUOTIENT[child['record']['caf']['quotient_q2']];

            tabs_body_record.querySelector(`.record-school`).innerHTML = child['record']['school'];
            tabs_body_record.querySelector(`.record-classroom`).innerHTML = classroom;
            tabs_body_record.querySelector(`.record-quotient-q1`).innerHTML = quotient_q1;
            tabs_body_record.querySelector(`.record-quotient-q2`).innerHTML = quotient_q2;
        }

    },


    updateProducts: function(children, snippets) {
        for (var i = 0; i < children.length; ++i) {
            if (children[i]['record']['classroom'] >= 1 &&
                children[i]['record']['classroom'] <= 4) {

                document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-products`).innerHTML = snippets['snippets_m6'];
            }
            else if (children[i]['record']['classroom'] >= 5 &&
                children[i]['record']['classroom'] <= 9) {

                document.querySelector(`.tabs-body-child[data-index="${i}"] .tabs-body-child-products`).innerHTML = snippets['snippets_p6'];
            }
            else {
                console.log(`Error: Unknow classroom (${children[i]['record']['classroom']}) for child: ${children[i]['first_name'] + ' ' + children[i]['last_name']}`);
            }
        }
    },


    updateEvents: function (e) {
        e.querySelectorAll('.Tabs-header-item')
            .forEach((item) => {
                item.addEventListener('click', this.updateEvents_onClick);
            });
    },
};


/**
 * Products
 * Generate a snippet for a given type and product
 *  types
 *      main
 *      normal
 *      expired
 *      breaking
 *      summary
 *      selected
 *      purchased
 *      summary-ok
 *      summary-ban
 */
var Product = {

    createProduct: function (type, product) {
        return `<li class="product-tile ${type}" data-id="${product.id}">
            <div class="product-tile-head">
                <div class="product-meta-title">${product.name}</div>
            </div>
        
            <div class="product-tile-body">
                <div class="product-meta-add"><i class="fas fa-plus"></i></div>
                <div class="product-meta-ban"><i class="fas fa-ban"></i></div>
                <div class="product-meta-check"><i class="fas fa-check"></i></div>
                <div class="product-meta-selected"><i class="fas fa-cart-arrow-down"></i></div>
                <div class="product-meta-checkbox"><input type="checkbox" onclick=""/></div>
            </div>
        
            <div class="product-tile-footer">
                <div class="product-meta-price">${product.price} E</div>
                <div class="product-meta-bought">payé le <span></span></div>
            </div>
        </li>`;
    },
}


var Modal = {

};


var Ticket = {};


/*
switch (state) {
            case 'Children':
                break;

            case 'Parent':
                window.localStorage.removeItem('parent');
                window.location.href = './Children.html';
                break;

            case 'Shop':
                window.localStorage.removeItem('cart');
                window.location.href = './Parent.html';
                break;

            case 'Summary':
                window.location.href = './Shop.html';
                break;

            case 'Payment':
                break;

            case 'Receipt':
                break;

            default:
                break;
        }
        */