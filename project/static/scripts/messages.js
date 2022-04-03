var default_container = '';

function Messages (id = default_container) {
    if (!id) return 'ID is not set.';

    const _el = document.getElementById(id);
    if (!_el) return 'ID not found.';
    // console.log(this);

    const log = {
        success: {
            write (name, message, {form = _el} = {}) {
                log.write(name, message, {
                    form: form,
                    type: 'success'
                });
            },
    
            deleteMessage (name, {form = _el} = {}) {
                log.deleteMessage(name, {
                    form: form,
                    type: 'success'
                });
            },
    
            clearMessages ({form = _el} = {}) {
                log.clearMessages({
                    form: form,
                    type: 'success'
                });
            },
        },

        warning: {
            write (name, message, {form = _el} = {}) {
                log.write(name, message, {
                    form: form,
                    type: 'warning'
                });
            },
    
            deleteMessage (name, {form = _el} = {}) {
                log.deleteMessage(name, {
                    form: form,
                    type: 'warning'
                });
            },
    
            clearMessages ({form = _el} = {}) {
                log.clearMessages({
                    form: form,
                    type: 'warning'
                });
            },
        },
    
        error: {
            write (name, message, {form = _el} = {}) {
                log.write(name, message, {form: form});
            },
    
            deleteMessage (name, {form = _el} = {}) {
                log.deleteMessage(name, {form: form});
            },
    
            clearMessages ({form = _el} = {}) {
                log.clearMessages({form: form});
            },
        },
    
        write (name, message, {
            type = 'error',
            form = _el
        } = {}) {
            let item = document.querySelector(`li[name="${name}"]`);
            if (!item) {
                item = document.createElement('li');
                item.setAttribute('name', name);
            }
            item.innerHTML = message;
            // console.log(item);
            
            form.classList.add(type);
        
            // Add item to list
            form.querySelector(`.${type}.message .list`).appendChild(item);
        },
    
        deleteMessage (name, {
            type = 'error',
            form = _el
        } = {}) {
    
            const list = form.querySelector(`.${type}.message .list`);
            if (list) {
    
                const item = list.querySelector(`li[name="${name}"]`);
                if (item) {
                    list.removeChild(item);
    
                    // If no item left remove error to form
                    if (!list.children.length) form.classList.remove(type);
                }
            }
        },
        
        clearMessages ({
            type = 'error',
            form = _el
        } = {}) {
    
            // Clear messages
            form.querySelector(`.${type}.message .list`).innerHTML = '';
    
            // Remove error to form classes
            form.classList.remove(type);
    
            return true;
        },
    };

    return log;
}