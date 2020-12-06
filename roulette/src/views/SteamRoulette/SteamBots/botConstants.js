
export const authErrors = {
    invalidPassword: 0,
    captcha: 1,
    emailCode: 2,
    twoFactorCode: 3,
    guardSetupCode: 4,
    success: 5,
    webAuthSession: 6
}

export const botStatuses = {
    active: 0,
    deleted: 1,
    needGuard: 2,
}

export const getStatusClass = status => {
  switch (status) {
    case botStatuses.active:
      return 'btn-success'
    case botStatuses.deleted:
      return 'btn-secondary'
    case botStatuses.needGuard:
      return 'btn-warning'
  }
}

export const getStatusTitle = status => {
  switch (status) {
    case botStatuses.active:
      return 'Active'
    case botStatuses.deleted:
      return 'Deleted'
    case botStatuses.needGuard:
      return 'Need Guard setup'
  }
}