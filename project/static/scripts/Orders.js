var Fetcher = {
    init: function() {
        this.events();
    },

    events: function() {
        document.getElementById('Fetcher-id-submit')
            .addEventListener('click', Fetcher.inputID_onSubmit);

        document.getElementById('Fetcher-date-submit')
            .addEventListener('click', Fetcher.inputDate_onSubmit);
    },

    inputID_onSubmit: function(e) {
        const value = document.getElementById('Fetcher-id-input').value;

        console.log(value);

        Orders.fromID(value);
    },

    inputDate_onSubmit(e) {
        const value = document.getElementById('Fetcher-date-input').value;

        console.log(value);

        Orders.fromDate(value);
    },


};


var Orders = {
    init: function (productHelper) {
        // this.BASE_URL = window.localStorage.getItem('BASE_URL');
        // this.token = window.localStorage.getItem('auth_token');
        // this.caster = JSON.parse(window.localStorage.getItem('caster'));

        this.BASE_URL = App.BASE_URL;
        this.token = App.token;
        this.caster = App.caster;

        this.productHelper = productHelper;

        this.products = undefined;

        if (!this.BASE_URL ||
            !this.token ||
            !this.caster) {
            console.log('No token, caster or BASE URL. Abort.');
            return false;
        }

        // Old
        // Products
        // this.products_ready = false;
        // this.initProducts();
        this.products_ready = true;

        return true;
    },

    initProducts: function() {
        var self = this;

        this._get('/v1/params/details')
        .then((data) => {
            self.products = data.school_year.product;
            self.products_ready = true;
            console.log(`Products ready with length: ${self.products.length}.`);


        })
        .catch((err) => {
            console.log('Failed to get products.');
        });
    },

    // Perform a request on ID
    fromID: function(id) {
        console.log('...');
        if (!this.products_ready)
            return false;

        var self = this;

        this._get(`/api/orders/${id}/details`)
        .then((data) => {
            self.orders = {};
            self.orders[data.order.id] = data.order;
            console.log(data.order);
            
            self._resetOrders();
            self.updateOrders();
        })
        .catch((err) => {
            console.log(`Failed to get order for id ${id} with error`);
            console.log(err);
        });
    },

    // Perform a request on Date
    fromDate(date) {
        if (!this.products_ready)
            return false;

        var self = this;

        this._get(`/api/order/date/${date}`)
            .then((data) => {
                self.orders = {};
                for (let order of data.orders)
                    self.orders[order.id] = order;

                console.log(self.orders);
                self._resetOrders();
                self.updateOrders();

                Collections.render(this.orders, this.products);
            })
            .catch((err) => {
                console.log(`Failed to get order for date ${date} with error`);
                console.log(err);
            });
    },

    // Perform a request on parameters
    fromParameters: function(parameters) {},

    // Fill orders HTML list
    updateOrders: function() {
        this._updateOrders(this.orders);
    },

    // Clean orders HTML list
    resetOrders: function() {
        this.orders = {};
        this._resetOrders();
    },

    createOrder(id) {
        console.log(this.orders[id]);
        Order.update(this.orders[id], this.products);
    },

    createCollections() {
        Collections.render(this.orders, this.products);
    },


    _updateOrders: function(orders) {
        const wrapper = document.querySelector('#Fetcher .Orders-wrapper');

        const keys = Object.keys(orders);
        for (let i in keys) {
            const order = orders[keys[i]];

            console.log(Object.keys(orders));

            // Handle status
            let _status = 'UNKNOW';
            const status = this._updateOrders_findLastStatus(order.status);

            switch (status.status) {
                case 1:
                    _status = 'EN COURS';
                    break;

                case 2:
                    _status = 'COMPLET';
                    break;

                case 3:
                    _status = 'REPORTE';
                    break;

                case 4:
                    _status = 'REPORTE';
                    break;

                case 5:
                    _status = 'ANNULE';
                    break;

                default:
                    break;
            }

            // 
            let fullname = '';
            if (order.payer)
                fullname = order.payer.first_name + ' ' + order.payer.last_name;

            // Create ticket
            wrapper.innerHTML += this._updateOrders_createItem(
                order.id,
                order.payer,
                order.amount,
                order.date,
                _status,
                order.tickets.length,
                fullname
            );

            // Handle payer
            // this._updateOrders_getParent(order.payer);

        }

        // Update events
        wrapper.querySelectorAll('.Orders-item').forEach((item) => {
            item.addEventListener('click', Orders.order_onClick);
        });
    },

    _updateOrders_findLastStatus: function(statuses) {
        return statuses[0];

        // Old
        let index = -1;
        let last_date = null;

        for (let i in statuses) {
            const status = statuses[i];

            if (!last_date) {
                index = i;
                last_date = new Date(status.date);
            }
            else {
                const cur = new Date(status.date);

                if (cur > last_date) {
                    index = i;
                    last_date = cur;
                }
            }
        }

        return statuses[index];
    },

    _updateOrders_createItem: function(id = 0, payer = 0, amount = 0, date = '././.', status = 'UNKNOW', tickets_len = 0, fullname = '') {
        return `<div class="Orders-item" data-id="${id}" data-payer="${payer}">
                    #${id} - <span class="Orders-fullname">${fullname}</span> - ${amount}€ - ${date} - ${status} - ${tickets_len} produit(s)
                </div>`;
    },

    _updateOrders_getParent: function(id) {
        var self = this;

        this._get(`/users/${id}`)
        .then((data) => {
            self._updateOrders_updateParent(id, data.user.last_name + ' ' + data.user.first_name);
        })
        .catch((err) => {
            console.log(`Failed to get parent for ID: ${id} with error:`);
            console.log(err);
        });
    },

    _updateOrders_updateParent: function(id, fullname = 'John Doe') {
        document.querySelector(`.Orders-item[data-payer="${id}"] span.Orders-fullname`)
            .innerHTML = fullname;
    },

    _resetOrders: function() {
        const wrapper = document.querySelector('#Fetcher .Orders-wrapper');

        wrapper.innerHTML = '';
    },

    order_onClick(e) {
        const id = e.target.getAttribute('data-id');
        // Orders.createOrder(id);

        window.open('/intern/order/print/' + id);
    },


    // Base API
    _get: function (url) {
        let self = this;
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${self.BASE_URL}${url}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${self.token}`,
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


    _post: function (url, payload) {
        let self = this;
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `${self.BASE_URL}${url}`,
                method: 'POST',
                data: JSON.stringify(payload),
                headers: {
                    Authorization: `Bearer ${self.token}`,
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
};


var Order = {

    init: function () {
        this.BASE_URL = window.localStorage.getItem('BASE_URL');
        this.token = window.localStorage.getItem('auth_token');
        this.caster = JSON.parse(window.localStorage.getItem('caster'));

        if (!this.BASE_URL ||
            !this.token ||
            !this.caster) {
            console.log('No token, caster or BASE URL. Abort.');
            return false;
        }

        return true;
    },

    update(order, products = []) {
        if (!this.products_ready) {
            this.products = products;
            this.products_ready = true;
        }



        const modal = document.getElementById('Order');

        // Show modal
        modal.classList.add('show');

        // Set modal title
        modal.querySelector('.modal-title span').innerHTML = order.id;

        // Set modal body
        modal.querySelector('.modal-body').innerHTML = this.updateContent(order);


        // Handle print event
        modal
            .querySelector('.btn.btn-info')
            .addEventListener('click', () => Order.print());

        // Handle closing events
        modal
            .querySelector('.close')
            .addEventListener('click', () => Order.close());

        modal
            .querySelector('.btn.btn-danger')
            .addEventListener('click', () => Order.close());
    },

    updateContent(order) {
        return `<div class="Order-content">
                    <link rel="stylesheet" href="./Common.css" />
                    <link rel="stylesheet" href="./Orders.css" />
                    <div class="container">
                        <div class="t-row">
                            ${this.updateIntels(order)}
                        </div>
            
                        <div class="t-row">
                            ${this.updateMethods(order['methods'])}
                        </div>
            
                        <div class="t-row t-children">                
                            ${this.updateChildren(order)}
                        </div>
                    </div>
                </div>`;
    },


    updateIntels(order) {
        this._updateParent(order.payer);

        let id = order.id;
        if (order.reference)
            id = order.reference;

        return `<fieldset class="t-fieldset t-intels">
                    <legend class="t-legend">Informations</legend>
                    <span class="t-inline-block"><b>ID: </b>${id}</span>
                    <span class="t-inline-block"><b>Date: </b>${Utils.orderDate(order.date)}</span>
                    <span class="t-inline-block"><b>Emetteur: </b>${this.caster.last_name + ' ' + this.caster.first_name}</span>
                    <span class="t-inline-block"><b>Parent: </b><span class="Order-parent-names"></span></span>
                </fieldset>`;
    },


    updateMethods(methods) {
        let snippet = '';

        for (let i in methods) {
            const method = methods[i];
            switch (method['method']) {
                case 1:
                    snippet += `<fieldset class="t-fieldset t-method">
                                        <legend class="t-legend">Espèce</legend>
                                        <span>${method['amount']} €</span>
                                    </fieldset>`;
                    break;

                case 2:
                    snippet += `<fieldset class="t-fieldset t-method">
                                        <legend class="t-legend">Chèque</legend>
                                        <span class="t-block">${method['amount']} €</span>
                                        <span class="t-block">${method['reference']}</span>
                                    </fieldset>`;
                    break;

                default:
                    break;
            }
        }

        return snippet;
    },


    updateChildren(order) {
        let children = {};

        for (let i in order['tickets']) {
            const ticket = order['tickets'][i];

            if (!children[ticket.payee]) {
                children[ticket.payee] = [];
            }

            children[ticket.payee].push(ticket);
        }

        let snippet = '';
        for (let i in children) {
            snippet += this.updateChild(i, children[i]);
        }

        return snippet;
    },


    updateChild(id, tickets) {
        // Handle products
        let snippet = '';

        for (let i in tickets) {
            const ticket = tickets[i];

            // Handle product
            let product = {};
            for (let j in this.products) {
                if (this.products[j].id === ticket.product) {
                    product = this.products[j];
                    break;
                }
            }

            const _name = (product.category !== 1) ? this._productName(product.name) : product.name;

            snippet += `<li class="t-product">
                                <span class="t-bold">${this._categoryToName(product.category)}</span>
                                <span>${_name}</span>
                                <span>${ticket.price}E</span>
                            </li>`;
        }

        // Handle child - record
        this._updateChild(id);
        this._updateRecord(id);

        return `<fieldset class="t-fieldset t-child" data-id="${id}">
                    <legend class="t-legend"><span class="Order-child-names"></span> - <span class="Order-child-record"></span></legend>
                    <ul class="t-products">
                        ${snippet}
                    </ul>
                </fieldset>`;
    },

    print() {
        const x = document.querySelector('#Order .Order-content');

        const w = window.open();
        w.document.write(`<div id="Order">${x.innerHTML}</div>`);
        // w.document.links.
        // w.print();
        // w.close();
    },

    close() {
        document.getElementById('Order').classList.remove('show');
    },


    _updateParent(id) {
        this._get(`/users/${id}`)
        .then((data) => {
            document.querySelector('#Order span.Order-parent-names').innerHTML = data.user.last_name + ' ' + data.user.first_name;
        })
        .catch((err) => {
            console.log(`Failed to get parent for ID: ${id} with error:`);
            console.log(err);
        });
    },

    _updateChild(id) {
        this._get(`/users/${id}`)
            .then((data) => {
                document.querySelector(`#Order .t-child[data-id="${id}"] span.Order-child-names`).innerHTML = data.user.last_name + ' ' + data.user.first_name;
            })
            .catch((err) => {
                console.log(`Failed to get child for ID: ${id} with error:`);
                console.log(err);
            });
    },

    _updateRecord(id) {
        this._get(`/v1/records/child/${id}`)
            .then((data) => {
                const r = data.record;
                const c = Order._classroomToName(r.classroom);
                const q1 = Order._quotientToName(r.caf.quotient_q1);
                const q2 = Order._quotientToName(r.caf.quotient_q2);

                document.querySelector(`#Order .t-child[data-id="${id}"] span.Order-child-record`).innerHTML = `${r.school} - ${c} - ${q1}/${q2}`;
            })
            .catch((err) => {
                console.log(`Failed to get record for ID: ${id} with error:`);
                console.log(err);
            });
    },


    _classroomToName(classroom) {
        const CLASSROOMS = [
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
        ];
        return CLASSROOMS[classroom];
    },


    _quotientToName(quotient) {
        const QUOTIENT = [
            '',
            'NE',
            'Q2',
            'Q1',
        ];
        return QUOTIENT[quotient];
    },


    _categoryToName(category) {
        const ICATEGORY = [
            '',
            'Périscolaire',
            'Janvier',
            'Février',
            'Mars',
            'Avril',
            'Mai',
            'Juin',
            'Juillet',
            'Aout',
            'Septembre',
            'Octobre',
            'Novembre',
            'Décembre',
            'Toussaint',
            'Noël',
            'Carnaval',
            'Paques',
            'Juillet (vacances)',
            'Aoüt (vacances)',
        ];
        return ICATEGORY[category];
    },


    _productName(name) {
        const x = name.split(' ');
        return x[0] + ' ' + x[1];
    },


    // Base API
    _get: function (url) {
        let self = this;
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${self.BASE_URL}${url}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${self.token}`,
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


    _post: function (url, payload) {
        let self = this;
        return new Promise((resolve, reject) => {
            $.ajax({
                url: `${self.BASE_URL}${url}`,
                method: 'POST',
                data: JSON.stringify(payload),
                headers: {
                    Authorization: `Bearer ${self.token}`,
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
};


var Collections = {

    init: function () {
        // this.BASE_URL = window.localStorage.getItem('BASE_URL');
        // this.token = window.localStorage.getItem('auth_token');
        // this.caster = JSON.parse(window.localStorage.getItem('caster'));

        this.BASE_URL = App.BASE_URL;
        this.token = App.token;
        this.caster = App.caster;

        if (!this.BASE_URL ||
            !this.token ||
            !this.caster) {
            console.log('No token, caster or BASE URL. Abort.');
            return false;
        }

        return true;
    },

    render(orders, products) {
        console.log(orders);
        console.log(Object.keys(orders).length);

        console.log(products);

        // FIX CASTER FILTERING
        this.children = {};

        for (let i in orders) {
            const order = orders[i];

            // Parse order ID
            let id = '';
            if (order.reference) {
                id = order.reference;
            }
            else {
                id = 'SITE_' + order.id;
            }

            // Add Type Carnet
            let carnet = 'ANTENNE';
            if (order.type == 2)
                carnet = 'DIRECTRICE';


            // Parse tickets
            for (let j in order.tickets) {
                const ticket = order.tickets[j];

                // Group children IDs
                if (!this.children[ticket.payee]) {
                    this.children[ticket.payee] = {};
                }

                if (!this.children[ticket.payee][id]) {

                    this.children[ticket.payee][id] = { 
                        carnet: carnet,
                        products: [] 
                    };
                }

                // Add product
                this.children[ticket.payee][id]['products'].push(ticket.product);


                // Add/Parse methods
                this.children[ticket.payee][id]['chk'] = '';
                this.children[ticket.payee][id]['esp'] = '';
                this.children[ticket.payee][id]['ref'] = '';
                this.children[ticket.payee][id]['credit'] = '';

                for (let k in order.methods) {
                    const method = order.methods[k];

                    // CASH
                    if (method.method === 1)
                        this.children[ticket.payee][id]['esp'] = method.amount;

                    else if (method.method === 2) {
                        this.children[ticket.payee][id]['chk'] = method.amount;
                        this.children[ticket.payee][id]['ref'] = method.reference;
                    }
                    else if (method.method === 5) {
                        this.children[ticket.payee][id]['credit'] = method.amount;
                    }
                }
            }
        }

        // console.log(this.children[332]);
        // console.log(this.children[474]);

        for (let i in this.children) {
            const child = this.children[i];

            for (let j in child) {

                console.log('Children ' + j);

                console.log(child[j]['products']);

                this.createRow(
                    j,
                    i,
                    child[j].carnet,
                    child[j].esp,
                    child[j].chk,
                    child[j].credit,
                    this.productToPeriod(products, child[j]['products']),
                    child[j].ref,
                );

                // this._updateChild(i);
                this._updateRecord(i);
                this._updateChild_v2(i);
            }
        }

        return;

        // OLD
        
        this.children = {};

        for (let i in orders) {
            const order = orders[i];

            if (order.caster.id !== 551) {
                continue;
            }

            // Parse order ID
            let id = '';
            if (order.reference) {
                id = order.reference;
            }
            else {
                id = 'SITE_' + order.id;
            }

            // Add Type Carnet
            let carnet = 'ANTENNE';
            if (order.order_type === 2)
                carnet = 'DIRECTRICE';


            // Parse tickets
            for (let j in order.tickets) {
                const ticket = order.tickets[j];

                // Group children IDs
                if (!this.children[ticket.payee]) {
                    this.children[ticket.payee] = {};
                }

                if (!this.children[ticket.payee][id]) {

                    this.children[ticket.payee][id] = { 
                        carnet: carnet,
                        products: [] 
                    };
                }

                // Add product
                this.children[ticket.payee][id]['products'].push(ticket.product);


                // Add/Parse methods
                this.children[ticket.payee][id]['chk'] = '';
                this.children[ticket.payee][id]['esp'] = '';
                this.children[ticket.payee][id]['ref'] = '';
                this.children[ticket.payee][id]['credit'] = '';

                for (let k in order.methods) {
                    const method = order.methods[k];

                    // CASH
                    if (method.method === 1)
                        this.children[ticket.payee][id]['esp'] = method.amount;

                    else if (method.method === 2) {
                        this.children[ticket.payee][id]['chk'] = method.amount;
                        this.children[ticket.payee][id]['ref'] = method.reference;
                    }
                    else if (method.method === 5) {
                        this.children[ticket.payee][id]['credit'] = method.amount;
                    }
                }
            }
        }

        // console.log(this.children[332]);
        // console.log(this.children[474]);

        for (let i in this.children) {
            const child = this.children[i];

            for (let j in child) {

                console.log('Children ' + j);

                console.log(child[j]['products']);

                this.createRow(
                    j,
                    i,
                    child[j].carnet,
                    child[j].esp,
                    child[j].chk,
                    child[j].credit,
                    this.productToPeriod(products, child[j]['products']),
                    child[j].ref,
                );

                // this._updateChild(i);
                this._updateRecord(i);
                this._updateChild_v2(i);
            }
        }


        this.createRow(
            '##########',
            '###########',
            '##########',
            '##########',
            '##########',
            '##########',
            '#########',
            '###########',
        );


        this.children = {};

        for (let i in orders) {
            const order = orders[i];

            if (order.caster.id !== 552) {
                continue;
            }

            // Parse order ID
            let id = '';
            if (order.reference) {
                id = order.reference;
            }
            else {
                id = 'SITE_' + order.id;
            }

            // Add Type Carnet
            let carnet = 'ANTENNE';
            if (order.order_type === 2)
                carnet = 'DIRECTRICE';


            // Parse tickets
            for (let j in order.tickets) {
                const ticket = order.tickets[j];

                // Group children IDs
                if (!this.children[ticket.payee]) {
                    this.children[ticket.payee] = {};
                }

                if (!this.children[ticket.payee][id]) {

                    this.children[ticket.payee][id] = { 
                        carnet: carnet,
                        products: [] 
                    };
                }

                // Add product
                this.children[ticket.payee][id]['products'].push(ticket.product);


                // Add/Parse methods
                this.children[ticket.payee][id]['chk'] = '';
                this.children[ticket.payee][id]['esp'] = '';
                this.children[ticket.payee][id]['ref'] = '';
                this.children[ticket.payee][id]['credit'] = '';

                for (let k in order.methods) {
                    const method = order.methods[k];

                    // CASH
                    if (method.method === 1)
                        this.children[ticket.payee][id]['esp'] = method.amount;

                    else if (method.method === 2) {
                        this.children[ticket.payee][id]['chk'] = method.amount;
                        this.children[ticket.payee][id]['ref'] = method.reference;
                    }
                    else if (method.method === 5) {
                        this.children[ticket.payee][id]['credit'] = method.amount;
                    }
                }
            }
        }

        // console.log(this.children[332]);
        // console.log(this.children[474]);

        for (let i in this.children) {
            const child = this.children[i];

            for (let j in child) {

                console.log('Children ' + j);

                console.log(child[j]['products']);

                this.createRow(
                    j,
                    i,
                    child[j].carnet,
                    child[j].esp,
                    child[j].chk,
                    child[j].credit,
                    this.productToPeriod(products, child[j]['products']),
                    child[j].ref,
                );

                // this._updateChild(i);
                this._updateRecord(i);
                this._updateChild_v2(i);
            }
        }
    },


    parseChildren(order) {
        for (let i in order.tickets) {
            const ticket = order.tickets[i];

            if (this.children[ticket.payee])
                this.children[ticket.payee] = [];
        }
    },


    createRow(order_id, child_id, carnet, esp, chk, avoir, period, ref) {
        const x = document.querySelector('.Collections .Collections-table tbody');

        const tr = document.createElement('tr');
            tr.setAttribute('data-child', child_id);
            tr.setAttribute('data-order', order_id);

        tr.innerHTML = `<th class="c-ticket-fullname"></th>
                        <th>${order_id}</th>
                        <th>${carnet}</th>
                        <th class="c-ticket-class"></th>
                        <th>${esp}</th>
                        <th>${chk}</th>
                        <th>${avoir}</th>
                        <th></th>
                        <th>${period}</th>
                        <th>${ref}</th>`;

        x.appendChild(tr);
    },


    productToPeriod(products, child_products) {
        const categories = {};

        for (let i in child_products) {

            for (let j in products) {

                if (child_products[i] === products[j].id) {

                    if (!categories[products[j].category]) {
                        categories[products[j].category] = [];
                    }

                    categories[products[j].category].push(products[j]);
                    break;
                }
            }
        }

        console.log(categories);

        // console.log(categories);

        let period = '';

        for (let i in categories) {
            const category = categories[i];

            console.log(category);

            // console.log(i);
            
            if (parseInt(i) === 1) {
                
                for (let j = 0; j < category.length; ++j) {
                    console.log(category[j].name);

                    if (j !== 0) {

                        period += ' + ';
                    }

                    period += category[j].name;
                }
            }
            else {
                if (period) {
                    period += ' ';
                }

                const _ = [
                    '',
                    '',
                    'mercredi(s) JANVIER',
                    'mercredi(s) FEVRIER',
                    'mercredi(s) MARS',
                    'mercredi(s) AVRIL',
                    'mercredi(s) MAI',
                    'mercredi(s) JUIN',
                    'mercredi(s) JUILLET',
                    'mercredi(s) AOUT',
                    'mercredi(s) SEPTEMBRE',
                    'mercredi(s) OCTOBRE',
                    'mercredi(s) NOVEMBRE',
                    'mercredi(s) DECEMBRE',
                    'jour(s) TOUSSAINT',
                    'jour(s) NOEL',
                    'jour(s) CARNAVAL',
                    'jour(s) PAQUES',
                    'jour(s) GRDS VACANCES JUILLET',
                    'jour(s) GRDS VACANCES AOUT',
                ];

                if (period)
                    period + ' + ';

                period += `${category.length} ${_[i]}`;
            }
        }

        console.log(period);

        return period;
    },


    _updateChild(id) {
        this._get(`/users/${id}`)
            .then((data) => {
                document
                    .querySelectorAll(`.Collections tr[data-child="${id}"] .c-ticket-fullname`)
                    .forEach((item) => {
                        item.innerHTML = data.user.last_name + ' ' + data.user.first_name;
                    });
            })
            .catch((err) => {
                console.log(`Failed to get child for ID: ${id} with error:`);
                console.log(err);
            });
    },


    _updateRecord(id) {
        // this._get(`/v1/records/child/${id}`)
        App.get(`/api/record/?child=${id}`, true)
            .then((data) => {
                console.log(data);

                const r = data.records;

                if (data.records.length) {
                    document
                        .querySelectorAll(`.Collections tr[data-child="${id}"] .c-ticket-class`)
                        .forEach((item) => {
                            item.innerHTML = data.records[0].school;
                        });
                }

            })
            .catch((err) => {
                console.log(`Failed to get record for ID: ${id} with error:`);
                console.log(err);
            });
    },

    _updateChild_v2 (id) {
        // this._get(`/api/user/${id}/`)
        App.get(`/api/user/${id}/`, true)
            .then((data) => {
                console.log(data);

                document
                    .querySelectorAll(`.Collections tr[data-child="${id}"] .c-ticket-fullname`)
                    .forEach((item) => {
                        item.innerHTML = data.user.last_name + ' ' + data.user.first_name;
                    });
                
                if (data.user.record) {
                    document
                        .querySelectorAll(`.Collections tr[data-child="${id}"] .c-ticket-class`)
                        .forEach((item) => {
                            item.innerHTML = data.user.record.school;
                        });
                }
            })
            .catch((err) => {
                console.log(`Failed to get child for ID: ${id} with error:`);
                console.log(err);
            });
    },


    _classroomToName(classroom) {
        const CLASSROOMS = [
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
        ];
        return CLASSROOMS[classroom];
    },


    // Base API
    _get: function (url) {
        let self = this;
        return new Promise(function (resolve, reject) {
            $.ajax({
                url: `${self.BASE_URL}${url}`,
                method: 'get',
                headers: {
                    Authorization: `Bearer ${self.token}`,
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
};