document.addEventListener('DOMContentLoaded', function() {
    const setReminderForm = document.getElementById('setReminderForm');
    const timezoneForm = document.getElementById('timezoneForm');
    const messageElement = document.getElementById('message');
    const remindersList = document.getElementById('remindersList');
    const timezoneMessageElement = document.getElementById('timezone_message');

    // =================================================================
    // 1. ЛОГИКА ФОРМЫ ЧАСОВОГО ПОЯСА
    // =================================================================
    if (timezoneForm) {
        timezoneForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const newTimezone = document.getElementById('timezone_select').value;
            
            timezoneMessageElement.classList.add('hidden');
            timezoneMessageElement.textContent = '';

            try {
                const response = await fetch('/api/update_profile', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        timezone: newTimezone
                    })
                });

                const result = await response.json();
                
                timezoneMessageElement.classList.remove('hidden');
                if (response.ok) {
                    timezoneMessageElement.textContent = result.message;
                    timezoneMessageElement.className = 'message-success';
                    // Обновляем страницу, чтобы отобразить новый часовой пояс
                    setTimeout(() => window.location.reload(), 1500); 
                } else {
                    timezoneMessageElement.textContent = result.error || 'Ошибка при сохранении часового пояса.';
                    timezoneMessageElement.className = 'message-error';
                }

            } catch (error) {
                console.error('Ошибка:', error);
                timezoneMessageElement.textContent = 'Ошибка соединения с сервером.';
                timezoneMessageElement.className = 'message-error';
                timezoneMessageElement.classList.remove('hidden');
            }
        });
    }


    // =================================================================
    // 2. ЛОГИКА ФОРМЫ НАПОМИНАНИЙ
    // =================================================================
    if (setReminderForm) {
        setReminderForm.addEventListener('submit', async function(e) {
            e.preventDefault();

            const medName = document.getElementById('med_name').value;
            const reminderTime = document.getElementById('reminder_time').value;
            const reminderEmail = document.getElementById('reminder_email').value;
            const frequency = document.getElementById('frequency').value; 
            const slot = document.getElementById('slot').value; 

            try {
                const response = await fetch('/api/set_reminder', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        med_name: medName,
                        reminder_time: reminderTime,
                        reminder_email: reminderEmail,
                        frequency: frequency,
                        slot: slot
                    })
                });

                const result = await response.json();

                messageElement.classList.remove('hidden');
                if (response.ok) {
                    messageElement.textContent = result.message;
                    messageElement.className = 'message-success';
                    setReminderForm.reset();
                    loadReminders(); 
                } else {
                    messageElement.textContent = result.error || 'Произошла ошибка при сохранении.';
                    messageElement.className = 'message-error';
                }

            } catch (error) {
                console.error('Ошибка:', error);
                messageElement.textContent = 'Ошибка соединения с сервером.';
                messageElement.className = 'message-error';
                messageElement.classList.remove('hidden');
            }
        });

        loadReminders();
    }
    
    // =================================================================
    // 3. ЛОГИКА ЗАГРУЗКИ И УДАЛЕНИЯ НАПОМИНАНИЙ
    // =================================================================
    async function loadReminders() {
        if (!remindersList) return;
        
        try {
            const response = await fetch('/api/get_reminders');
            
            if (response.status === 401) {
                remindersList.innerHTML = '<p>Авторизуйтесь, чтобы увидеть напоминания.</p>';
                return;
            }

            const reminders = await response.json();

            remindersList.innerHTML = '';
            
            if (reminders.length === 0) {
                remindersList.innerHTML = '<p>Напоминаний пока нет. Установите первое!</p>';
                return;
            }

            const frequencyMap = {
                'daily': 'Ежедневно',
                'once': 'Однократно'
            };

            reminders.forEach(reminder => {
                const item = document.createElement('div');
                item.className = 'card reminder-item';
                item.innerHTML = `
                    <div>
                        <h4>${reminder.med_name}</h4>
                        <p class="time">${reminder.time}</p>
                        <small>Слот: ${reminder.slot} | ${frequencyMap[reminder.frequency]} | На ${reminder.email}</small>
                    </div>
                    <button class="btn-icon" onclick="deleteReminder(${reminder.id})">❌</button>
                `;
                remindersList.appendChild(item);
            });

        } catch (error) {
            console.error('Ошибка загрузки напоминаний:', error);
            remindersList.innerHTML = '<p>Не удалось загрузить напоминания.</p>';
        }
    }

    window.deleteReminder = async function(id) {
        if (confirm('Вы уверены, что хотите удалить это напоминание?')) {
             try {
                const response = await fetch(`/api/delete_reminder/${id}`, {
                    method: 'POST'
                });
                if (response.ok) {
                    loadReminders();
                } else {
                    alert('Ошибка при удалении напоминания.');
                }
            } catch (error) {
                console.error('Ошибка при удалении:', error);
            }
        }
    }
});