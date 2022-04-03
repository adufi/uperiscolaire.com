function getPrice (intel, product) {
    let price = product.price;
    let quotient = 0;

    const categories_q1 = [10, 11, 12, 13, 14, 15];

    if (product.category !== 0 && product.category !== 1) {
        if (categories_q1.includes(product.category)) {
            quotient = intel.quotient_1;
        }
        else {
            quotient = intel.quotient_2;
        }
    }

    if (quotient === 2) {
        price = product.price_q2;
    }
    else if (quotient === 3) {
        price = product.price_q1;
    }

    return price;
}



class Product {
    constructor () {
        this._products = {};
        this._categories = {};
        
        // SLUGS and ANCHORS
        this.CATEGORIESSLUG = [
            'UNSET',
            'PERISCOLAIRE',
            'SEPTEMBRE',
            'OCTOBRE',
            'TOUSSAINT',
            'NOVEMBRE',
            'DECEMBRE',
            'NOEL',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'CARNAVAL',
            'AVRIL',
            'PAQUES',
            'MAI',
            'JUIN',
            'JUILLET',
            'GRDS_VACANCES_JUILLET',
            'AOUT',
            'GRDS_VACANCES_AOUT'
        ];

        this.CATEGORIESNAME = [
            'AUCUNE CATEGORIE',
            'PERISCOLAIRE',
            'SEPTEMBRE',
            'OCTOBRE',
            'TOUSSAINT',
            'NOVEMBRE',
            'DECEMBRE',
            'NOEL',
            'JANVIER',
            'FEVRIER',
            'MARS',
            'CARNAVAL',
            'AVRIL',
            'PAQUES',
            'MAI',
            'JUIN',
            'JUILLET',
            'GRDS. VACANCES JUILLET',
            'AOUT',
            'GRDS. VACANCES AOUT'
        ];

        this.TYPES = [
            'UNSET',
            'PERISCOLAIRE',
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
            'GRDS_VACANCES_AOUT'
        ];
    }

    //  
    init (raw) {
        const parsed = raw;
        // const parsed = JSON.parse(raw);

        // Prepare categories
        for (let i = 0; i < this.CATEGORIESSLUG.length; ++i) {
            this._categories[this.CATEGORIESSLUG[i]] = {
                'name': this.CATEGORIESNAME[i],
                'products': []
            };
        }

        // Products
        // Categories
        for (let i = 0; i < parsed.length; ++i) {
            const product = parsed[i];

            // Add product into a dictionnary
            this._products[product['id']] = product;

            // Add category
            const category = product['category'];
            const slug = this.TYPES[category];

            // if (!this._categories[category])
            //     this._categories[category] = {
            //         'name': this.CATEGORIES[category],
            //         'anchor': this.ANCHORS[category],
            //         'products': []
            //     };
            
            this._categories[slug]['products'].push(product.id);

            continue;
            

            if (category === 1) {    
                if (!this.categories[category]) {
                    this.categories[category] = [];
                }
                this.categories[category].push(product.id);
            }
            else {
                const sub = product['subcategory'];

                if (!this.categories[category]) {
                    this.categories[category] = {};
                }

                if (!this.categories[category][sub]) {
                    this.categories[category][sub] = [];
                }

                this.categories[category][sub].push(product.id);
            }
        }
    }

    get (id) {return this._products[id]; }
    category (id) { return this._categories[id]; }

    products () { return this._products; }
    categories () { return this._categories; }


    /**
     * NEW
     * 
     * Product case
     *  normal
     *  normal - stock short
     *  normal - stock empty
     *  selected
     *  ticket
     */

    render (type, product, child_id=0) {
        const li = document.createElement('li');

        let stock = '';
        if (product.hasOwnProperty('category') &&
            product.hasOwnProperty('stock_max') &&
            product.hasOwnProperty('stock_current')) {
            
            if (product.category > 1) {
                stock = `<div class="product-meta-stock">Stock: ${product.stock_current} / ${product.stock_max}</div>`;
            }
        }

        li.className = 'product-tile ' + type;
        li.setAttribute('data-id', getAttr(product, 'id', 0));
        li.setAttribute('data-child', child_id);

        let price = getAttr(product, 'price', 0);

        li.innerHTML = `
        <div class="product-tile-head">
            <div class="product-meta-title">${product.name}</div>
            ${stock}
        </div>
    
        <div class="product-tile-body">
            <div class="product-meta-add"><i class="fas fa-plus"></i></div>
            <div class="product-meta-ban"><i class="fas fa-ban"></i></div>
            <div class="product-meta-check"><i class="fas fa-check"></i></div>
            <div class="product-meta-selected"><i class="fas fa-cart-arrow-down"></i></div>
            <div class="product-meta-checkbox"><input type="checkbox" onclick=""/></div>
        </div>
    
        <div class="product-tile-footer">
            <div class="product-meta-price">${price} €</div>
            <div class="product-meta-bought">payé le <span></span></div>
        </div>`;

        return li;
    }


    /**
     * UI
     */
    
    createFromProduct (type, product, intel, onClick) {
        const li = document.createElement('li');

        let stock = '';
        if (product.category > 1) {
            stock = `<div class="product-meta-stock">Stock: ${product.stock_current} / ${product.stock_max}</div>`;
        }

        li.className = 'product-tile ' + type;
        li.setAttribute('data-id', product.id);

        let price = getPrice(intel, product);

        li.innerHTML = `<div class="product-tile-head">
                <div class="product-meta-title">${product.name}</div>
                ${stock}
            </div>
        
            <div class="product-tile-body">
                <div class="product-meta-add"><i class="fas fa-plus"></i></div>
                <div class="product-meta-ban"><i class="fas fa-ban"></i></div>
                <div class="product-meta-check"><i class="fas fa-check"></i></div>
                <div class="product-meta-selected"><i class="fas fa-cart-arrow-down"></i></div>
                <div class="product-meta-checkbox"><input type="checkbox" onclick=""/></div>
            </div>
        
            <div class="product-tile-footer">
                <div class="product-meta-price">${price} €</div>
                <div class="product-meta-bought">payé le <span></span></div>
            </div>`;

        return li;
    }

    createFromTicket (type, product, ticket, onClick) {
        const li = document.createElement('li');

        li.className = 'product-tile ' + type;
        li.setAttribute('data-id', product.id);

        li.innerHTML = `<div class="product-tile-head">
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
                <div class="product-meta-price">${ticket.price} €</div>
                <div class="product-meta-bought">payé le <span></span></div>
            </div>`;

        return li;
    }

    updateProductType (type, product, child) {
        const eproduct = document.querySelector(`.Tabs-body-child[data-id="${child}"] .product-tile[data-id="${product}"]`);

        if (eproduct) {

            // if (!ticket.status) {
            //     console.log(`No status for ticket with payee (${child}) and product (${product}).`);
            //     return;
            // }

            switch (type) {
                case 'selected':
                    this._selected(eproduct);
                    break;
    
                case 'purchased':
                    this._purchased(eproduct, );
                    break;
            }
        }
    }

    updateFromTicket(ticket) {
        const eproduct = document.querySelector(`.Tabs-body-child[data-id="${ticket.payee}"] .product-tile[data-id="${ticket.product}"]`);
        // console.log(eproduct);
        
        if (eproduct) {
            if (!ticket.status) {
                console.log(`No status for ticket with payee (${ticket.payee}) and product (${ticket.product}).`);
                return;
            }
    
            // Status are ordered by desc date (the last 1st)
            const status = ticket.status[0];
    
            switch (status.status) {
                case 0:
                    break;
    
                // RESERVED
                case 1:
                    this._reserved(eproduct, ticket.price, status.date);
                    break;
    
                // BOUGHT
                case 2:
                    this._purchased(eproduct, ticket.price, status.date);
                    break;
            }
        }
    }

    
    _selected (eproduct) {
        eproduct.className = 'product-tile selected';

        // eproduct.querySelector('.product-tile-body').innerHTML = 'RESERVE';
        // eproduct.querySelector('.product-meta-bought').innerHTML = App.Utils.dateTimeToHTML(date);
    }

    _reserved (eproduct, price, date) {
        eproduct.className = 'product-tile reserved';

        eproduct.querySelector('.product-tile-body').innerHTML = 'RESERVE';
        eproduct.querySelector('.product-meta-bought').innerHTML = App.Utils.dateTimeToHTML(date);
    }
    
    _purchased (eproduct, price, date) {
        eproduct.className = 'product-tile purchased';
        
        eproduct.querySelector('.product-meta-bought').innerHTML = App.Utils.dateTimeToHTML(date);
    }

    _summary_ok (eproduct) {
        eproduct.className = 'product-tile summary-ok';
        
        // eproduct.querySelector('.product-meta-bought').innerHTML = App.Utils.dateTimeToHTML(date);
    }

    _summary_ban (eproduct) {
        eproduct.className = 'product-tile summary-ban';
    }
}