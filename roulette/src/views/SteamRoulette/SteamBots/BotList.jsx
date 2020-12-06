import React, {useEffect} from 'react'
import {Link, useHistory} from 'react-router-dom';
import {
  CBadge,
  CCard,
  CCardBody,
  CCardHeader,
  CCol,
  CDataTable, CPagination,
  CRow
} from '@coreui/react'

import aio from "../../../aio";
import {botStatuses} from "./botConstants";

const getStatus = status => {
  switch (status) {
    case botStatuses.active:
      return 'success'
    case botStatuses.deleted:
      return 'secondary'
    case botStatuses.needGuard:
      return 'warning'
  }
}

const getStatusTitle = status => {
  switch (status) {
    case botStatuses.active:
      return 'Active'
    case botStatuses.deleted:
      return 'Deleted'
    case botStatuses.needGuard:
      return 'Need Guard setup'
  }
}
const fields = ['id', 'username', 'date_created', 'date_modified', 'status']

const ItemLink = ({item, field}) => {
  const uri = `/bot/${item.id}`;
  return (
    <td>
      <Link to={uri}>{item[field]}</Link>
    </td>
  )
}

const BotList = ({match}) => {
  const [state, setState] = React.useState({botList: null, isLoading: true, page: parseInt(match.params.page || 1)})
  let history = useHistory();
  const perPage = 100;

  const fetchData = async () => {
    setState({...state, isLoading: true})
    const {data, status} = await aio.get(`/admin/api/trade-bots/list/${state.page}?per_page=${perPage}`);
    const pages = Math.ceil(data.items_count / perPage);
    setState(
    (state) => {
      return {
        ...state,
        isLoading: !state.isLoading,
        botList: data.bots,
        itemCount: data.items_count,
        pages,
      }
    })
  };

  useEffect(() => {
    fetchData();
  }, [state.page])

  const onPagesChange = (page) => {
    history.push(`/bots/list/${page}`);
    setState({...state, page})
  }
  return (
  <>
    <CRow>
      <CCol>
        <CCard>
          <CCardHeader>
            Bot list
          </CCardHeader>
          <CCardBody>
            <CDataTable
              items={state.botList}
              fields={fields}
              dark
              hover
              striped
              bordered
              size="sm"
              loading={state.isLoading}
              scopedSlots={{
                'status':
                (item) => (
                  <td>
                    <CBadge color={getStatus(item.status)}>
                      {getStatusTitle(item.status)}
                    </CBadge>
                  </td>
                ),
                'username': (item) => <ItemLink item={item} field="username"/>
              }}
            />
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
    <CRow>
      <CCol>
        <CCard>
          <CCardBody>
            <CPagination
              activePage={state.page}
              pages={state.pages}
              onActivePageChange={(i) => onPagesChange(i)}
            />
          </CCardBody>
        </CCard>
      </CCol>
    </CRow>
  </>
  )
}

export default BotList
